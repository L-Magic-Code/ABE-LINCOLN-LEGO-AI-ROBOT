import ev3_dc as ev3
import time
import asyncio
import edge_tts
import uuid
import os
import subprocess
import threading
import random
import vosk
import sounddevice
import json
import cv2
import ultralytics
import mediapipe
import math
from google import genai
import sys
from PIL import Image
import tkinter as tk
import customtkinter as ctk

opened_files_list = []
config_file = open("PROJECT_ROOT/External_Files/config.json", "r")
opened_files_list.append("config.json")
config_str = config_file.read()
config_file.close()
opened_files_list.remove("config.json")
config = json.loads(config_str)


if config["vosk_file_type"] == "medium":
    VOSK_MODEL_PATH = config["vosk_small_file"]
elif config["vosk_file_type"] == "large":
    VOSK_MODEL_PATH = config["vosk_large_file"]
else:
    raise Exception("There is no defined vosk_file_type in the config file, or it is a typo!")  
VOICE_MODEL = config["voice"]
model = vosk.Model(VOSK_MODEL_PATH)
recognizer = vosk.KaldiRecognizer(model, 16000)

is_speaking = False
reading = False
what_was_last_said = ''
what_was_just_said = ''
camera = cv2.VideoCapture(0)
mp_hands = mediapipe.solutions.hands
Hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=.75, static_image_mode=False)
Face = mediapipe.solutions.face_detection.FaceDetection()
MediaPipe_Draw = mediapipe.solutions.drawing_utils
camera_tracking_mode = config["default_tracking_mode"]
chat = client.chats.create(model=config["gemini_model"])
client = genai.Client(api_key=config["api_key"])
run_eyes = True
listen = False
trigger_words = ["hey abe", "hey abraham", "abe", "abraham", "president lincoln", "president abe", "president abraham"]
capture_frame = config["auto_camera_start"]
run_camera_loop = True
vision_trigger_words = config["vision-trigger-words"]
use_mic = config["use_mic"]
latest_frame_description = ''
detect_object = ultralytics.YOLO("yolo26x.pt")
previous_alert = ''
ctk.set_appearance_mode("system")
abe_window = ctk.CTk(className="Abe Control Center")
abe_window_icon = tk.PhotoImage("PROJECT_ROOT/Window_Icon.png")
abe_window.iconphoto(True, abe_window_icon)
abe_window.geometry("850x650")
abe_window.title("Abe Control Center")
abe_window.resizable(0, 0)

status_text = ctk.CTkLabel(abe_window, text="STATUS:", font=("Arial", 30))
status_text.place(x=370, y=3)

control_text = ctk.CTkLabel(abe_window, text="CONTROL:", font=("Arial", 30))
control_text.place(x=368, y=225)

alerts_text = ctk.CTkLabel(abe_window, text="Alerts:   None", font=("Nimbus Sans Narrow", 27))
alerts_text.place(x=500, y=40)

tracking_mode_text = ctk.CTkLabel(abe_window, text=f"Tracking mode:   {camera_tracking_mode}", font=("Nimbus Sans Narrow", 27))
tracking_mode_text.place(x=12, y=40)

listening_text = ctk.CTkLabel(abe_window, text=f"Listening:   {listen}", font=("Nimbus Sans Narrow", 27))
listening_text.place(x=12, y=80)

mic_on_text = ctk.CTkLabel(abe_window, text=f"Mic on:   {use_mic}", font=("Nimbus Sans Narrow", 27))
mic_on_text.place(x=12, y=120)

opened_files_text = ctk.CTkLabel(abe_window, text=f"Opened Files:   {opened_files_list}", font=("Nimbus Sans Narrow", 27))
opened_files_text.place(x=500, y=80)

def set_alert(alert=''):
    if alert == previous_alert:
        return
    alerts_text.configure(text="Alerts:   " + alert)

def set_tracking_text(tracking_text=''):
    tracking_mode_text.configure(text="Tracking mode:   " + tracking_text)

def update_listening_text():
    listening_text.configure(text="Listen:   " + listen)

def update_mic_on_text():
    mic_on_text.configure(text=f"Mic on:   {use_mic}")

def update_opened_files_text():
    opened_files_text.configure(text=f"Opened Files:   {opened_files_list}")
    time.sleep(.5)

def change_config(key, property):
    global config
    global opened_files_list
    config_file = open("PROJECT_ROOT/External_Files/config.json", "r")
    opened_files_list.append("config.json")
    update_opened_files_text()
    config_str = config_file.read()
    config_file.close()
    opened_files_list.remove("config.json")
    update_opened_files_text()
    config = json.loads(config_str)
    config[key] = property
    config_file = open("PROJECT_ROOT/External_Files/config.json", "w")
    opened_files_list.append("config.json")
    update_opened_files_text()
    json.dump(config, config_file)
    config_file.close()
    opened_files_list.remove("config.json")
    update_opened_files_text()

def open_hand(hand, speed=75):
    if hand.position != 180:
        if not hand.busy:
            hand.move_to(180, speed=speed, brake=True).start(thread=False)

def close_hand(hand, speed=75):
    if hand.position != 0:
        if not hand.busy:
            hand.move_to(0, speed=speed, brake=True).start(thread=False)

def left_grab():
    if not left_hand.busy:
        left_hand.start_move(speed=25)
        while not left_fingers.touched:
            time.sleep(.01)
        left_hand.stop()

def right_grab():
    if not right_hand.busy:
        right_hand.start_move(speed=25)
        while not right_fingers.touched:
            time.sleep(.01)
        right_hand.stop()

def grab():
    global right_hand_empty
    global left_hand_empty
    if right_hand_empty:
        open_hand(right_hand)
        while not right_fingers.touched:
            time.sleep(.01)
        close_hand(right_hand)
        right_hand_empty = False
        change_config("right_hand_empty", False)
        return True
    elif left_hand_empty:
        open_hand(left_hand)
        while not left_fingers.touched:
            time.sleep(.01)
        close_hand(left_hand)
        left_hand_empty = False
        change_config("left_hand_empty", False)
        return True
    else:
        return False

def move_mouth_up_and_down():
    global is_speaking
    open_mouth(25, speed=25)
    while is_speaking:
        random_degree = random.randrange(5, 17)
        intensity = random.randrange(5, 17)
        close_mouth(random_degree, speed=intensity, brake=True)
        time.sleep(.07)
        open_mouth(random_degree, speed=intensity, brake=True)
        time.sleep(.07)
    close_mouth(25, speed=25, brake=True)

def eyes_read():
    global reading
    while reading:
        eyes.move_to(60, speed=1).start(thread=False)
        eyes.move_by(150, speed=45).start(thread=False)

def deliver_gettysburg_address():
    global opened_files_list
    open_file = open(config["gettysburg_address_file_path"])
    opened_files_list.append(config["gettysburg_address_file_path"])
    update_opened_files_text()
    gettysburg_address = open_file.read()
    open_file.close()
    opened_files_list.remove(config["gettysburg_address_file_path"])
    right_hand.stop()
    update_opened_files_text()
    mouth_say("Alright, I shall now deliver the gettysburg address.")

    if not left_fingers.touched or not right_fingers.touched:
        mouth_say("Luke, can you please give me my speech?")
        time.sleep(.5)
        open_hand(left_hand)
        open_hand(right_hand)
        while not left_fingers.touched:
            time.sleep(.01)
        if left_fingers.touched:
            close_hand(left_hand)
        while not right_fingers.touched:
            time.sleep(.01)
        if right_fingers.touched:
            close_hand(right_hand)
        mouth_say("Thank you.")
    try:
        time.sleep(1)
        reading = True
        threading.Thread(target=eyes_read).start()
        mouth_say(gettysburg_address)
        reading = False
        mouth_say("Thank you! Have a blessed Fourth Of July on our 250th anniversary of our country!")
    finally:
        right_hand.stop()

def callback(indata, frames, time, status):
    if recognizer.AcceptWaveform(bytes(indata)):
        result = recognizer.Result()
        dict_result = json.loads(result)
        global what_was_just_said
        what_was_just_said = dict_result['text']

def get_speech():
    global what_was_just_said
    global what_was_last_said
    if what_was_last_said != what_was_just_said:
        what_was_last_said = what_was_just_said
        return what_was_just_said
    else:
        what_was_last_said = what_was_just_said
        return ''

def move_eyes_to_position(position, speed=30):
    position = position / 1.65
    if not eyes.busy:
        eyes.move_to(position=round(position), speed=speed).start(thread=False)

def camera_window_loop():
    global run_eyes
    while run_camera_loop:
        if capture_frame == True:
            image_okay, frame = camera.read()
        else:
            time.sleep(.01)
            continue
        frame = cv2.flip(frame, 1)
        if not image_okay:
            raise ConnectionError("Camera not connected! Try disconnecting and reconnecting the camera cable!")
        
        if camera_tracking_mode == 'Face':
            results = Face.process(frame)
            if results.detections:
                for result in results.detections:
                    keypoints = result.location_data.relative_keypoints
                    nose = keypoints[2]
                    nose_x = nose.x - .5
                    nose_y = (nose.y - .4) * -1
                    raw_degrees = math.degrees(math.atan2(nose_y, nose_x))
                    degrees = (raw_degrees + 360) % 360
                    degrees = round(degrees)
                    if abs((degrees - (eyes.position * 1.65 % 360) + 180) % 360 - 180) >= 25:
                        if not eyes.busy:
                            if run_eyes:
                                move_eyes_to_position(position=degrees)
                    MediaPipe_Draw.draw_detection(frame, result)
                    break
        if camera_tracking_mode == 'Hand':
            results = Hands.process(frame)
            if results.multi_hand_landmarks:
                for result in results.multi_hand_landmarks:
                    center = result.landmark[9]
                    center_x = center.x - .5
                    center_y = (center.y - .4) * -1
                    raw_degrees = math.degrees(math.atan2(center_y, center_x))
                    degrees = (raw_degrees + 360) % 360
                    degrees = round(degrees)
                    if abs((degrees - (eyes.position * 1.65 % 360) + 180) % 360 - 180) >= 25:
                        if not eyes.busy:
                            if run_eyes:
                                move_eyes_to_position(position=degrees)
                    MediaPipe_Draw.draw_landmarks(frame, result, mp_hands.HAND_CONNECTIONS)
                    break

        cv2.imshow("Abe's Eyes:", frame)
        cv2.waitKey(1)

def add_to_history(role, text):
    global opened_files_list
    open_file = open("PROJECT_ROOT/External_Files/chat_history.txt", "a")
    opened_files_list.append("chat_history.txt")
    update_opened_files_text()
    open_file.write(role + ": " + text + '\n')
    open_file.close()
    opened_files_list.remove("chat_history.txt")
    update_opened_files_text()

def get_file_text(file):
    global opened_files_list
    opened_files_list.append(file)
    open_file = open(file, "r")
    update_opened_files_text()
    history = open_file.read()
    open_file.close()
    opened_files_list.remove(file)
    update_opened_files_text()
    return history

def complete_generated_function(function: str):
    global right_hand_empty
    global left_hand_empty
    global camera_tracking_mode
    if function == "grab_something":
        worked = grab()
        if not worked:
            open_hand(right_hand)
            right_hand_empty = True
            grab()
    elif function == "wave":
        if right_hand_empty and not right_arm.busy and not right_hand.busy:
            right_arm.move_by(degrees=75, speed=45, brake=True).start(thread=False)
            right_hand.start_move(speed=100)
            time.sleep(2)
            right_hand.stop()
            right_arm.move_by(degrees=-75, speed=45, brake=True).start(thread=False)
            close_hand(right_hand, speed=20)
        elif left_hand_empty and not left_arm.busy and not left_hand.busy:
            left_arm.move_by(degrees=75, speed=45, brake=True).start(thread=False)
            left_hand.start_move(speed=100)
            time.sleep(2)
            left_hand.stop()
            left_arm.move_by(degrees=-75, speed=45, brake=True).start(thread=False)
            close_hand(left_hand, speed=20)
    elif function == "look_at_users_hand":
        camera_tracking_mode = 'hand'
    elif function == "look_at_users_face":
        camera_tracking_mode = 'face'
    
def say_with_emotion(text, emotion):
    if emotion.lower() == 'happy':
        eyebrows.move_by(degrees=20).start(thread=False)    
    elif emotion.lower() == 'sad':
        eyebrows.move_by(degrees=18, speed=5).start(thread=False)
    elif emotion.lower() == 'angry':
        eyebrows.move_by(degrees=-10, speed=35).start(thread=False)
    mouth_say(text)
    if emotion.lower() == 'happy':
        eyebrows.move_by(degrees=-20).start(thread=False)    
    elif emotion.lower() == 'sad':
        eyebrows.move_by(degrees=18, speed=5).start(thread=False)
    elif emotion.lower() == 'angry':
        eyebrows.move_by(degrees=10, speed=35).start(thread=False)

def input_triggered_sight(str_input):
    for trigger in vision_trigger_words:
        if trigger in str_input:
            return True
    return False

def get_objects():
    global capture_frame
    capture_frame = False
    _, frame = camera.read()
    capture_frame = True
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output = "You see: "
    frame = Image.fromarray(frame)
    result = detect_object(frame, verbose=False)[0]
    for x in result.boxes:
        output = output + "a " + str(result.names[int(x.cls)] + ", ")
    return output

def shutdown():
    global run_camera_loop
    run_camera_loop = False
    time.sleep(5)
    move_eyes_to_position(0, 10)
    mic.close()
    camera.release()
    cv2.destroyAllWindows()
    mouth.move_to(0, speed=10).start(thread=False)
    sys.exit(0)

camera_loop = threading.Thread(target=camera_window_loop)
camera_loop.start()
mic = sounddevice.RawInputStream(
    samplerate=16000,
    blocksize=8000,
    dtype='int16',
    channels=1,
    callback=callback
)
history = get_file_text(config["chat_history_file_path"])
if  history != '':
    chat.send_message("Our conversation so far has been the following: \n" + history)

ai_prompt = get_file_text(config["prompt_file_path"])

if ai_prompt == '':
    raise SyntaxError("No AI Prompt! Please add a prompt for Abe in the file ai_prompt.txt!")
else:
    chat.send_message(ai_prompt)
mic.start()
print("Say \"Hey Abe\" to start talking to Abe!")
    
def main_loop():
    global listen
    global use_mic
    while True:
        #if use_mic:
         #   my_input = get_speech()
        my_input = input("You: ")
        if my_input == '':
            continue
        elif my_input.lower() == "shutdown":
            shutdown()
        print("You: " + my_input)
        if my_input.lower() in trigger_words:
            if listen == False:
                listen = True
                print("Abe is listening!")
            continue
        if listen and len(my_input)  >= 2:
            if input_triggered_sight(my_input):
                print("[Detected a vision-trigger-word! Sending vision description with prompt!]")
                my_input = f"You see: {get_objects()}. \n The user said: {my_input}"
            response = chat.send_message(my_input)
            response_text = response.text.split(None, 2)[2]
            response_words = response.text.split()
            print(response.text)
            function_thread = threading.Thread(target=complete_generated_function, args=[response_words[1]]) 
            function_thread.start()
            say_with_emotion(text=response_text, emotion=response_words[0])
            function_thread.join()
            add_to_history(role="User", text=my_input)
            add_to_history(role="Abe", text=response.text)
threading.Thread(target=main_loop).start()

abe_window.mainloop()
