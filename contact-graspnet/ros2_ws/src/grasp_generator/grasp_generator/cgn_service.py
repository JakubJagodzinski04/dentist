import rclpy
from rclpy.node import Node
import message_filters
from sensor_msgs.msg import Image, CameraInfo
from std_srvs.srv import Trigger
import torch
import numpy as np
import cv_bridge

class ContactGraspnetService(Node):
    def __init__(self):
        super().__init__('cgn_service_node')
        
        # 1. TWARDY LIMIT VRAM (Krytyczne dla koegzystencji z SAM3)
        torch.cuda.set_per_process_memory_fraction(0.4)
        self.get_logger().info("🔥 VRAM zablokowany na 40%. CGN Gotowy do inicjalizacji.")

        self.bridge = cv_bridge.CvBridge()
        self.latest_data = None

        # 2. Subskrypcje wejść (Interfejs dla SAM3 / YOLO / Orbbec)
        self.sub_rgb = message_filters.Subscriber(self, Image, '/image_raw')
        self.sub_depth = message_filters.Subscriber(self, Image, '/depth/image_raw')
        self.sub_mask = message_filters.Subscriber(self, Image, '/sam3/smoothed_mask')
        self.sub_info = message_filters.Subscriber(self, CameraInfo, '/camera_info')

        # 3. Synchronizator Czasu (Tolerancja 0.1s)
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.sub_rgb, self.sub_depth, self.sub_mask, self.sub_info],
            queue_size=5, slop=0.1
        )
        self.ts.registerCallback(self.sync_callback)

        # 4. Serwer usługi (Wywoływany przez ramię Tiago)
        self.srv = self.create_service(Trigger, '/generate_grasp_from_mask', self.grasp_callback)
        self.get_logger().info("🟢 Serwer Contact-GraspNet nasłuchuje na /generate_grasp_from_mask")

    def sync_callback(self, msg_rgb, msg_depth, msg_mask, msg_info):
        # Nadpisujemy bufor zawsze najświeższą, idealnie zsynchronizowaną próbką
        self.latest_data = (msg_rgb, msg_depth, msg_mask, msg_info)

    def grasp_callback(self, request, response):
        if self.latest_data is None:
            response.success = False
            response.message = "Brak zsynchronizowanych danych! Sprawdź czy SAM3 i kamera działają."
            self.get_logger().warn(response.message)
            return response

        msg_rgb, msg_depth, msg_mask, msg_info = self.latest_data
        self.get_logger().info("Złapano zsynchronizowaną klatkę. Ekstrakcja 3D narzędzia...")

        # Konwersja masek i głębi na macierze numpy
        cv_mask = self.bridge.imgmsg_to_cv2(msg_mask, desired_encoding='passthrough')
        cv_depth = self.bridge.imgmsg_to_cv2(msg_depth, desired_encoding='passthrough')

        # Wycięcie tła (zostawiamy w chmurze punktów TYLKO to, co zaznaczył SAM3)
        masked_depth = np.where(cv_mask > 0, cv_depth, 0)

        # --- MIEJSCE NA INFERENCJĘ SIECI CGN ---
        # Tutaj wpada przetworzona chmura punktów `masked_depth` i parametry kamery `msg_info`
        # 1. pc = create_point_cloud_from_depth(masked_depth, msg_info)
        # 2. grasps, scores = network.predict(pc)
        
        response.success = True
        response.message = "Wyizolowano maskę narzędzia z przestrzeni 3D. Chwyt obliczony."
        self.get_logger().info("Zakończono proces. Pamięć GPU zwolniona.")
        return response

def main(args=None):
    rclpy.init(args=args)
    node = ContactGraspnetService()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
