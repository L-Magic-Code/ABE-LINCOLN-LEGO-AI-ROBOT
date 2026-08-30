import cv2
import json
import mediapipe
import time
import math
import ultralytics
from PIL import Image
import picamera2
import threading
import random
import pathlib
from extra_functions import print_red
import numpy

class Camera:
    def __init__(self, camera_type, port=None, debug_level=1, force=False):
        """
        Returns Camera object. 
        'type' may be camera.pi_camera, or Camera
        """

        self.type = camera_type.lower()

        self.debug_level = debug_level

        self.stable = True

        self.latest_frame = numpy.zeros((720, 1280, 3), numpy.uint8)

        self.black_frame = numpy.zeros((720, 1280, 3), numpy.uint8)

        cv2.putText(self.black_frame, "CAMERA NOT CONNECTED", (360, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 1, cv2.LINE_AA)

        self.force = force

        if self.type == "raspberry_pi_camera":
            self.cam = picamera2.Picamera2()
            self.cam.start()
            if self.debug_level > 0:
                print("[vision_functions] [Debug] Testing camera connection...")
            try:
                self.get_frame()
            except TimeoutError:
                print_red("[vision_functions] [ERROR] Failed to connect to desk camera. Ignoring all desk camera calls")
                self.stable = False
            if self.stable:
                print("[vision_functions] [DEBUG] Connection to regular camera successfull!")


        elif self.type == "regular_camera":
            if type(port) not in [str, int]:
                raise Exception(f"camera_type must be str or int, not {type(self.type)}!")
            self.cam = cv2.VideoCapture(port)

            if self.debug_level > 0:
                print("[vision_functions] [Debug] Testing camera connection...")


            if not self.cam.isOpened():
                print_red("[vision_functions] [ERROR] Failed to connect to front camera. Ignoring all front camera calls")
                self.stable = False

            if self.stable:
                ret, _ = self.cam.read()
                if not ret:
                    print_red("[vision_functions] [ERROR] Failed to connect to front camera. Ignoring all front camera calls")
                    self.stable = False                
                else:
                    if self.debug_level > 0:
                        print("[vision_functions] [DEBUG] Connection to raspberry pi camera successfull!")

        elif self.type == "placeholder_camera":
            pass
        
        else:
            print_red(f"Unknown camera type: {self.type}.")
            self.stable = False
        
    def get_frame(self):
        if self.type == "raspberry_pi_camera":
            if self.stable:
                try:
                    self.latest_frame = self.cam.capture_array(wait=1)
                    self.latest_frame = cv2.cvtColor(self.latest_frame, cv2.COLOR_RGB2BGR)
                    return self.latest_frame
                except:
                    if self.force:
                        return self.black_frame
                    else:
                        return None
            else:
                if self.force:
                    return self.black_frame
                else:
                    return None
                
        elif self.type == "regular_camera":
            if self.stable:
                ret, frame = self.cam.read()
                if not ret:
                   raise ConnectionError("Failed to grab a frame. This might be because the camera is not connected.")
                return frame
            else:
                if self.force:
                    return self.black_frame
                else:
                    return None
        elif self.type == "placeholder_camera":
            if self.force:
                return self.black_frame
            else:
                return None

    def _loop(self):
        while True:
            self.latest_frame = self.get_frame()
            time.sleep(.01)

    def start_capture_loop(self):
        threading.Thread(target=self._loop).start()


class Vision:
    def __init__(self, abe : object = None, use_mindstorms=None, debug_level=1):
        """
        Abe's main vision class.
        Accepts 'Abe' class from ev3_functions.py.
        """
        BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
        self.pathlib_config_file = BASE_DIR / "External_Files" / "Config" / "vision_config.json"
        with open(self.pathlib_config_file, "r", encoding="utf-8") as opened_file:
            self.config = json.load(opened_file)

        self.capture_frame = self.config["auto_camera_start"]

        self.vision_trigger_words = self.config["vision_trigger_words"]

        self.abe = abe

        self.debug_level = debug_level

        self.use_front_camera = self.config["use_front_camera"]
        self.use_desk_camera = self.config["use_desk_camera"]


        if self.use_front_camera:
            self.front_camera = Camera(self.config["front_camera_type"], self.config["front_camera_port"], self.debug_level, self.config["force_front_camera"])
            self.front_camera.start_capture_loop()
        else:
            self.front_camera = Camera("placeholder_camera", self.config["force_front_camera"])
            if self.debug_level > 0:
                print("[vision_functions] [Info] Ignoring all front camera functions!")

        if self.use_desk_camera:
            self.desk_camera = Camera(self.config["desk_camera_type"], self.config["desk_camera_port"], self.debug_level, self.config["force_desk_camera"])
            self.desk_camera.start_capture_loop()
        else:
            self.desk_camera = Camera("placeholder_camera", self.config["force_desk_camera"])
            if self.debug_level == 1:
                print("[vision_functions] [Info] Ignoring all desk camera functions!")

        self.mp_hands = mediapipe.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=.75, static_image_mode=False)
        self.face = mediapipe.solutions.face_detection.FaceDetection()
        self.mediapipe_draw = mediapipe.solutions.drawing_utils
        self.camera_tracking_mode = self.config["default_tracking_mode"]
        self.run_camera_loop = True
        self.capture_frame = True
        self.move_eyes = True
        self.detect_object = ultralytics.YOLO("yolo26x.pt")
        self.use_mindstorms = use_mindstorms
        self.include_desk_feed = self.config["show_desk_feed"]
        self.include_front_feed = self.config["show_front_feed"]

    def _camera_windows_loop(self):
        """
        Abe's main camera loop.
        
        It will capture frames as long as the capture_frame attribute is True.

        Eye tracking depends on the camera_tracking_mode attribute, that may either be "face" or "hand" 
        """

        while self.run_camera_loop:
            if self.use_front_camera:
                if self.capture_frame == True:
                    self.frame = self.front_camera.latest_frame
                else:
                    time.sleep(.01)
                    continue
                if self.frame is None:
                    time.sleep(.01)
                    continue
                    

                self.frame = cv2.flip(self.frame, 1)

                if self.camera_tracking_mode == 'face':
                    self.results = self.face.process(self.frame)
                    if self.results.detections:
                        self.result = self.results.detections[0]
                        self.keypoints = self.result.location_data.relative_keypoints
                        self.nose = self.keypoints[2]
                        self.nose_x = self.nose.x - .5
                        self.nose_y = (self.nose.y - .4) * -1
                        self.raw_degrees = math.degrees(math.atan2(self.nose_y, self.nose_x))
                        self.degrees = (self.raw_degrees + 360) % 360
                        self.degrees = round(self.degrees)
                        if self.use_mindstorms:
                            if self.move_eyes:
                                if abs((self.degrees - self.abe.eyes.position + 180) % 360 - 180) >= 25:
                                    if not self.abe.eyes.busy:
                                        self.abe.move_eyes_to_position(position=self.degrees)
                        self.mediapipe_draw.draw_detection(self.frame, self.result)

                elif self.camera_tracking_mode == 'hand':
                    self.results = self.hands.process(self.frame)
                    if self.results.multi_hand_landmarks:
                        self.result = self.results.multi_hand_landmarks[0]
                        self.center = self.result.landmark[9]
                        self.center_x = self.center.x - .5
                        self.center_y = (self.center.y - .4) * -1
                        self.raw_degrees = math.degrees(math.atan2(self.center_y, self.center_x))
                        self.degrees = (self.raw_degrees + 360) % 360
                        self.degrees = round(self.degrees)
                        if self.use_mindstorms:
                            if self.move_eyes:
                                if abs((self.degrees - self.abe.eyes.position + 180) % 360 - 180) >= 25:
                                    if not self.abe.eyes.busy:
                                        self.abe.move_eyes_to_position(position=self.degrees)
                        self.mediapipe_draw.draw_landmarks(self.frame, self.result, self.mp_hands.HAND_CONNECTIONS)
                if self.include_front_feed:
                    cv2.imshow("Front Camera", self.frame)
                
            if self.use_desk_camera:
                self.desk_frame = self.desk_camera.get_frame()
                if self.desk_frame is not None:
                    cv2.imshow("Desk Camera", self.desk_frame)
            cv2.waitKey(1)

    def start_camera_windows_loop(self, thread : bool=True, include_desk_camera_feed=True):
        """
        Starts tracking faces or hands, and opens preview windows.
        Uses threading if 'thread' argument is True.
        """
        if thread == False:
            self._camera_windows_loop()
        else:
            threading.Thread(target=self._camera_windows_loop).start()

    def yolo_describe_frame(self, frame):
        """
        Uses YOLO to get a basic str of objects in frame.
        """
        self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.output = "You see: "
        self.frame = Image.fromarray(self.capture_frame)
        self.result = self.detect_object(frame, verbose=False)[0]
        for x in self.result.boxes:
            self.output = self.output + "a " + str(self.result.names[int(x.cls)] + ", ")
        return self.output

    def text_in_trigger_words(self, text : str=''):
        """
        Decides whether or not a vision trigger word is in 'text'.
        Returns the result as a bool AND the word that was in 'text'.
        """ 
        for trigger_word in self.vision_trigger_words:
            if trigger_word in text:
                return True, trigger_word
        if "hello" in text or "hi " in text: 
            if random.randrange(0, 1) == 0:
                return True, "hello / hi"
        return False, None

if __name__ == "__main__":
    vision = Vision(debug_level=2)
    vision.start_camera_windows_loop()
    while True:
        time.sleep(1)