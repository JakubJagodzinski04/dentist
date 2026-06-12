import rclpy
from rclpy.node import Node
import message_filters
from sensor_msgs.msg import Image
from visualization_msgs.msg import Marker, MarkerArray
import numpy as np
import cv2
import cv_bridge

class ContactGraspnetEventNode(Node):
    def __init__(self):
        super().__init__('cgn_event_node')
        
        self.is_computing = False
        self.bridge = cv_bridge.CvBridge()

        # Subskrypcje
        self.sub_rgb = message_filters.Subscriber(self, Image, '/image_raw')
        self.sub_depth = message_filters.Subscriber(self, Image, '/camera/depth/image_raw')
        self.sub_mask = message_filters.Subscriber(self, Image, '/sam3/smoothed_mask')

        # Synchronizator (Tolerancja czasowa 2 sekundy)
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.sub_rgb, self.sub_depth, self.sub_mask],
            queue_size=30, slop=2.0
        )
        self.ts.registerCallback(self.sync_callback)

        self.marker_pub = self.create_publisher(MarkerArray, '/cgn/grasp_markers', 10)
        self.get_logger().info("🟢 Węzeł CGN gotowy. Oczekuję na pierwszą maskę z SAM3...")

    def sync_callback(self, msg_rgb, msg_depth, msg_mask):
        if self.is_computing:
            return
            
        self.is_computing = True
        
        try:
            cv_mask = self.bridge.imgmsg_to_cv2(msg_mask, desired_encoding='passthrough')
            cv_depth = self.bridge.imgmsg_to_cv2(msg_depth, desired_encoding='passthrough')

            # 1. Bezwzględne spłaszczenie maski do 1 kanału (Rozwiązuje błąd OpenCV)
            if len(cv_mask.shape) == 3:
                cv_mask = cv_mask[:, :, 0]

            # 2. Zrównanie wymiarów (Wysokość x Szerokość)
            depth_h, depth_w = cv_depth.shape[:2]
            cv_mask_resized = cv2.resize(cv_mask, (depth_w, depth_h), interpolation=cv2.INTER_NEAREST)

            unique_ids = np.unique(cv_mask_resized)
            object_ids = unique_ids[unique_ids > 0]

            if len(object_ids) == 0:
                self.is_computing = False
                return
                
            first_object_id = object_ids[0]
            
            # 3. Maska jako mnożnik algebraiczny o typie głębi
            binary_mask = (cv_mask_resized == first_object_id).astype(cv_depth.dtype)

            # 4. Jeżeli głębia ma 3 kanały, powielamy maskę na 3 kanały dla wymnożenia
            if len(cv_depth.shape) == 3:
                binary_mask = np.expand_dims(binary_mask, axis=-1)

            # 5. Czyste matematyczne wycięcie (Algebra zamiast instrukcji warunkowych)
            isolated_depth = cv_depth * binary_mask

            self.get_logger().info(f"⚡ Przetwarzam 1st Crop (ID: {first_object_id}). GPU liczy...")
            
            self.publish_dummy_marker()

        except Exception as e:
            self.get_logger().error(f"Błąd przetwarzania: {e}")
            import traceback
            self.get_logger().error(traceback.format_exc())
        finally:
            self.is_computing = False

    def publish_dummy_marker(self):
        marker_array = MarkerArray()
        marker = Marker()
        marker.header.frame_id = "camera_link"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "grasps"
        marker.id = 0
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.pose.position.x = 0.0
        marker.pose.position.y = 0.0
        marker.pose.position.z = 0.5 
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
        self.get_logger().info("✅ Wynik w RViz2. GPU odblokowane.")

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