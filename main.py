#Hello
def main():
    import time
    from AbeFunctions import ev3_functions
    from AbeFunctions import vision_functons
    from AbeFunctions import gemini_functions
    from AbeFunctions import mic_functions
    from AbeFunctions import extra_functions
    import time
    import json

    with open("AbeOS 1.0/External_Files/Config/mic_config.json", "r") as opened_file:
        config = json.load(opened_file)

    abe = ev3_functions.Abe(use_mindstorms=True)
    gemini = gemini_functions.AI()
    vision = vision_functons.Vision(abe, use_mindstorms=True)
    vision.start_camera_windows_loop(thread=True)
    mic = mic_functions.Mic(debug_level=2)
    mic.start_listening()
    time.sleep(1)

    while True:
        print("[main] Say \"Hey Abe\" to start talking to Abe!")
        mic.wait_for_trigger_word(config["listen-trigger-words"])
        print("[main] Abe is listening!")
        timer = time.time()
        while True:
            if time.time() - timer >= config["listening-timeout"]:
                print("[main] Stopped listening!")
                break 
            prompt = mic.get_speech()
        
            if len(prompt.split()) < 3 or prompt == '':
                continue
            print(f"You: {prompt}")
            vision_triggered, trigger_word = vision.text_in_trigger_words(prompt)
            if vision_triggered:
                image = vision.get_frame('desk')
                emotion, function, response = gemini.get_response(prompt, image, trigger_word)
            else:
                emotion, function, response = gemini.get_response(prompt)
            #extra_functions.cool_print(f"[main] Abe: {emotion} {function} {response}", 2, thread=True)
            abe.say(response)
            timer = time.time() 

if __name__ == '__main__':
    main()

