import rclpy
from rclpy.node import Node
import message_filters
from sensor_msgs.msg import Image, CameraInfo, PointCloud2
from std_msgs.msg import Header
import sensor_msgs_py.point_cloud2 as pc2
from visualization_msgs.msg import Marker, MarkerArray
import numpy as np
import cv2
import cv_bridge

class ContactGraspnetEventNode(Node):
    def __init__(self):
        super().__init__('cgn_event_node')
        
        self.is_computing = False
        self.bridge = cv_bridge.CvBridge()

        # ==========================================
        # PARAMETRYZACJA WĘZŁA
        # ==========================================
        self.declare_parameter('use_mock_camera', False)
        self.use_mock = self.get_parameter('use_mock_camera').value

        # Subskrypcje wspólne dla obu trybów
        self.sub_rgb = message_filters.Subscriber(self, Image, '/image_raw')
        self.sub_depth = message_filters.Subscriber(self, Image, '/camera/depth/image_raw')
        self.sub_mask = message_filters.Subscriber(self, Image, '/sam3/smoothed_mask')

        self.marker_pub = self.create_publisher(MarkerArray, '/cgn/grasp_markers', 10)
        self.pc_pub = self.create_publisher(PointCloud2, '/cgn/tool_pointcloud', 10)

        # LOGIKA PRZEŁĄCZANIA TRYBÓW
        if self.use_mock:
            self.get_logger().warn("🟣 TRYB SYMULACJI (Mock). Ignoruję /camera_info. Duża tolerancja czasowa (slop=2.0).")
            self.ts = message_filters.ApproximateTimeSynchronizer(
                [self.sub_rgb, self.sub_depth, self.sub_mask],
                queue_size=30, slop=2.0
            )
            self.ts.registerCallback(self.sync_callback_mock)
        else:
            self.get_logger().info("🟢 TRYB SPRZĘTOWY (Live). Wymagam /camera/color/camera_info. Rygor czasowy (slop=0.1).")
            self.sub_info = message_filters.Subscriber(self, CameraInfo, '/camera/color/camera_info')
            self.ts = message_filters.ApproximateTimeSynchronizer(
                [self.sub_rgb, self.sub_depth, self.sub_mask, self.sub_info],
                queue_size=10, slop=0.1
            )
            self.ts.registerCallback(self.sync_callback_live)

    # Funkcje przekierowujące do głównego silnika
    def sync_callback_mock(self, msg_rgb, msg_depth, msg_mask):
        self.process_pipeline(msg_rgb, msg_depth, msg_mask, None)

    def sync_callback_live(self, msg_rgb, msg_depth, msg_mask, msg_info):
        self.process_pipeline(msg_rgb, msg_depth, msg_mask, msg_info)

    # Główny silnik obliczeniowy
    def process_pipeline(self, msg_rgb, msg_depth, msg_mask, msg_info):
        if self.is_computing:
            return
            
        self.is_computing = True
        
        try:
            cv_mask = self.bridge.imgmsg_to_cv2(msg_mask, desired_encoding='passthrough')
            cv_depth = self.bridge.imgmsg_to_cv2(msg_depth, desired_encoding='passthrough')

            if len(cv_mask.shape) == 3:
                cv_mask = cv_mask[:, :, 0]

            depth_h, depth_w = cv_depth.shape[:2]
            cv_mask_resized = cv2.resize(cv_mask, (depth_w, depth_h), interpolation=cv2.INTER_NEAREST)

            unique_ids = np.unique(cv_mask_resized)
            object_ids = unique_ids[unique_ids > 0]

            if len(object_ids) == 0:
                self.is_computing = False
                return
                
            first_object_id = object_ids[0]
            binary_mask = (cv_mask_resized == first_object_id).astype(cv_depth.dtype)

            if len(cv_depth.shape) == 3:
                box_dims = np.expand_dims(binary_mask, axis=-1)
                binary_mask = np.repeat(box_dims, cv_depth.shape[2], axis=-1)

            isolated_depth = cv_depth * binary_mask

            flat_mask = binary_mask[:, :, 0] if len(binary_mask.shape) == 3 else binary_mask
            v_coords, u_coords = np.where(flat_mask > 0)
            
            if len(v_coords) > 0:
                depths = isolated_depth[v_coords, u_coords]
                valid_idx = depths > 0
                u_valid = u_coords[valid_idx]
                v_valid = v_coords[valid_idx]
                depths_valid = depths[valid_idx]
                
                if len(depths_valid) > 0:
                    depths_m = np.where(depths_valid > 10.0, depths_valid / 1000.0, depths_valid).astype(np.float32)
                    
                    # LOGIKA MACIERZY OPTYCZNEJ
                    if msg_info is None:
                        # Wstrzyknięcie dla Mock Camera
                        fx, fy = 500.0, 500.0
                        cx, cy = depth_w / 2.0, depth_h / 2.0
                    else:
                        # Rzeczywisty odczyt z soczewki Orbbec
                        K = np.array(msg_info.k).reshape(3, 3)
                        fx, fy = float(K[0, 0]), float(K[1, 1])
                        cx, cy = float(K[0, 2]), float(K[1, 2])
                    
                    X = (u_valid - cx) * depths_m / fx
                    Y = (v_valid - cy) * depths_m / fy
                    Z = depths_m
                    
                    points_3d = np.column_stack((X, Y, Z))
                    c_x, c_y, c_z = np.mean(X), np.mean(Y), np.mean(Z)
                    
                    self.get_logger().info(f"🎯 Przetworzono chmurę: {len(points_3d)} punktów.")
                    
                    self.publish_pointcloud(points_3d)
                    self.publish_real_marker(c_x, c_y, c_z)
                else:
                    self.get_logger().warn("Brak prawidłowych odczytów głębi na masce.")
            else:
                self.get_logger().warn("Maska obiektu jest pusta.")

        except Exception as e:
            self.get_logger().error(f"Błąd rurociągu: {e}")
            import traceback
            self.get_logger().error(traceback.format_exc())
        finally:
            self.is_computing = False

    def publish_pointcloud(self, points):
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = "camera_link"
        pc_msg = pc2.create_cloud_xyz32(header, points.tolist())
        self.pc_pub.publish(pc_msg)

    def publish_real_marker(self, x, y, z):
        marker_array = MarkerArray()
        marker = Marker()
        marker.header.frame_id = "camera_link" 
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "grasps"
        marker.id = 0
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.pose.position.x = float(x)
        marker.pose.position.y = float(y)
        marker.pose.position.z = float(z) 
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.02
        marker.scale.y = 0.085
        marker.scale.z = 0.02
        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 0.0
        marker.color.a = 0.8
        marker_array.markers.append(marker)
        self.marker_pub.publish(marker_array)

def main(args=None):
    rclpy.init(args=args)
    node = ContactGraspnetEventNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()