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

class Vision:
    def __init__(self, abe : object = None, use_mindstorms=None):
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

        self.front_camera = cv2.VideoCapture(8)
        self.desk_camera = picamera2.Picamera2()

        self.mp_hands = mediapipe.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=.75, static_image_mode=False)
        self.face = mediapipe.solutions.face_detection.FaceDetection()
        self.mediapipe_draw = mediapipe.solutions.drawing_utils
        self.camera_tracking_mode = self.config["default_tracking_mode"]
        self.run_camera_loop = True
        self.capture_frame = True
        self.move_eyes = True
        self.detect_object = ultralytics.YOLO("yolo26x.pt")
        self.desk_camera.start()
        self.use_mindstorms = use_mindstorms

    def show(self, window_name, frame_array=None):
        """
        Uses cv2.imshow to create a window and display a numpy image array.
        """
        if frame_array == None:
            raise Exception("[vison_functions] Frame_array is None or not entered!")
        cv2.imshow(str(window_name), frame_array)

    def get_frame(self, camera):
        """
        Returns an numpy array captured by camera.
        'Camera' can either be 'front' or 'desk'. """
        if camera == "front":
            self.ret, self.frame = self.front_camera.read()
            if not self.ret:
                raise Exception("Camera not connected!")
            return self.frame
        elif camera == "desk":
            self.dframe = self.desk_camera.capture_array()
            self.dframe = cv2.cvtColor(self.dframe, cv2.COLOR_RGB2BGR)
            return self.dframe
        else:
            print(f"[vision_functions] Unknown camera: {camera}")

    def _camera_windows_loop(self, include_desk_feed=True):
        """
        Abe's main camera loop.
        
        It will capture frames as long as the capture_frame attribute is True.

        Eye tracking depends on the camera_tracking_mode attribute, that may either be "face" or "hand" """
        while self.run_camera_loop:
            if self.capture_frame == True:
                self.frame = self.get_frame("front")
            else:
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

            if self.camera_tracking_mode == 'hand':
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

            if include_desk_feed:
                self.desk_frame = self.get_frame("desk")
                cv2.imshow("Desk Camera", self.desk_frame)
            cv2.imshow("Front Camera", self.frame)
            cv2.waitKey(1)

    def start_camera_windows_loop(self, thread : bool=True, include_desk_camera_feed=True):
        """
        Starts tracking faces or hands, and opens preview windows.
        Uses threading if 'thread' argument is True.
        """
        if thread == False:
            self._camera_windows_loop(include_desk_camera_feed)
        else:
            threading.Thread(target=self._camera_windows_loop, args=[include_desk_camera_feed]).start()

    def yolo_describe_frame(self, frame):
        """
        Uses YOLO to get a basic str of objects in frame."""
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        self.output = "You see: "
        self.frame = Image.fromarray(self.capture_frameframe)
        self.result = self.detect_object(self.frame, verbose=False)[0]
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
    vision = Vision(use_mindstorms=False)
    vision.start_camera_windows_loop()
