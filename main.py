def main():
    from AbeFunctions import ev3_functions
    from AbeFunctions import vision_functons
    from AbeFunctions import gemini_functions
    from AbeFunctions import mic_functions
    from AbeFunctions import extra_functions
    import time
    import json
    import pathlib

    BASE_DIR = pathlib.Path(__file__).resolve().parent

    with open(BASE_DIR / "External_Files" / "Config" / "mic_config.json", "r",  encoding="utf-8") as opened_file:
        config = json.load(opened_file)

    USE_MINDSTORMS = True
    USE_MIC = config["use_mic"]

    abe = ev3_functions.Abe(USE_MINDSTORMS)
    print("[main] Waiting for key to be inserted...")
    abe.wait_for_key_insert()
    print("[main] Starting...")
    gemini = gemini_functions.AI()
    vision = vision_functons.Vision(abe, USE_MINDSTORMS)
    vision.start_camera_windows_loop(thread=True)
    functionHandeler = extra_functions.function_calling_handeler(abe, vision)
    if USE_MIC:
        mic = mic_functions.Mic(debug_level=2)
        mic.start_listening() 
    abe.home_motors()
    time.sleep(1)

    while abe.key_sensor.touched:
        if USE_MIC:
            print("[main] Say \"Hey Abraham Lincoln\" to start talking to Abe!")
            mic.wait_for_trigger_word(config["listen-trigger-words"])
            print("[main] Abe is listening!")
        timer = time.time()
        while True:
            if time.time() - timer >= config["listening-timeout"] and USE_MIC:
                print("[main] Stopped listening!")
                break 
            if USE_MIC:
                prompt = mic.get_speech()
            else:
                prompt = input("[main] You: ")
        
            if len(prompt.split()) < 3 and USE_MIC or prompt == '':
                continue
            if USE_MIC:
                print(f"You: {prompt}")
            vision_triggered, trigger_word = vision.text_in_trigger_words(prompt)
            if vision_triggered:
                image = vision.get_gemini_img()
                emotion, function, response = gemini.get_response(prompt, image, trigger_word)
            else:
                emotion, function, response = gemini.get_response(prompt)
            abe.move_to_emotion(emotion)
            functionHandeler.complete_function(function)
            abe.say(response)
            abe.move_to_neutral()
            extra_functions.cool_print(f"[main] Abe: {function} {response}", 4, thread=False, delay=3.5)
            timer = time.time() 

if __name__ == '__main__':
    main()

