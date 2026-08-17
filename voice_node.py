import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import threading
import audioop

class VoiceNode(Node):
    def __init__(self):
        super().__init__('voice_node')
        
        self.voice_pub = self.create_publisher(String, '/voice_command', 10)
        self.tts_sub = self.create_subscription(
            String, '/robot_tts', self.tts_callback, 10)
            
        self.is_robot_speaking = False
        self.get_logger().info("Inicjalizacja modelu Vosk...")

        model_path = "/tiago_ws/src/tiago_pick_place/models"
        
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            
            # Używamy fonetycznych zapisów słów (np. "ten" zamiast "10")
            grammar = '["robot", "pass", "k six", "k eight", "k ten", "take"]'
            self.recognizer.SetGrammar(grammar)
            
        except Exception as e:
            self.get_logger().error(f"Błąd ładowania modelu Vosk: {e}")
            return

        self.audio_queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self.audio_loop, daemon=True)
        self.thread.start()
        
        self.get_logger().info("Mikrofon uruchomiony. Czekam na słowo 'Robot'...")

    def tts_callback(self, msg):
        self.is_robot_speaking = True
        self.create_timer(3.0, self.unmute)

    def unmute(self):
        self.is_robot_speaking = False

    def audio_loop(self):
        def callback(indata, frames, time, status):
            if status and "overflow" not in str(status):
                self.get_logger().warn(f"Audio status: {status}")
            self.audio_queue.put(bytes(indata))

        # Automatyczne wykrywanie domyślnego sample rate systemu
        try:
            device_info = sd.query_devices(sd.default.device[0], 'input')
            actual_rate = int(device_info['default_samplerate'])
            self.get_logger().info(f"Wykryto domyślny samplerate urządzenia: {actual_rate} Hz")
        except Exception as e:
            self.get_logger().warn(f"Nie udało się zapytać o samplerate, używam 44100 Hz: {e}")
            actual_rate = 44100

        target_rate = 16000
        state = None
        
        try:
            with sd.RawInputStream(samplerate=actual_rate, blocksize=8000, dtype='int16',
                                   channels=1, callback=callback):
                while self.running and rclpy.ok():
                    data = self.audio_queue.get()
                    
                    # Resampling do 16000 Hz dla Voska
                    resampled_data, state = audioop.ratecv(data, 2, 1, actual_rate, target_rate, state)
                    
                    if self.recognizer.AcceptWaveform(resampled_data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '')
                        
                        if text and text != '[unk]':
                            self.process_text(text)
        except Exception as e:
            self.get_logger().error(f"Błąd urządzenia audio: {e}")

    def process_text(self, text):
        self.get_logger().info(f'Usłyszano: {text}')
        
        if "robot" in text:
            command = text.replace("robot", "").strip()
            if command:
                msg = String()
                msg.data = command
                self.voice_pub.publish(msg)
                self.get_logger().info(f'Wysłano komendę do Mózgu: {command}')

def main(args=None):
    rclpy.init(args=args)
    node = VoiceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.running = False
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()