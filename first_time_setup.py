"""
Welcome to Abe's first time setup!
You should only ever need to run this code once.

This code will create files:
1. ai_prompt.txt file
2. chat_history.txt

ai_prompt.txt creation:
    This will make a text file with a basic prompt for Abe (The AI). 
    This will be sent to AI at the start of the main program to tell Abe who he is. 
    You may edit the ai prompt file to personalize it. However, it is important that you do not change the format of the response, as it will foul up how the response is prosessed.

chat_history.txt creation:
    This will make an empty text file for conversation history. 
    This will be sent to AI at the start of the main program to tell Abe the conversation so far if it is set to in the gemini_config file.
    Even if you don't plan to use conversation saving, it is a good idea to create the empty file.
    You can always delete anything in the history file.
"""

import json 
import pathlib

print("[first_time_setup] Starting!")
default_prompt = '''You are Abe, a Lego AI Abraham Lincoln robot.
You will never output any markdown or formatted text of any kind. 
You also never use any emojis or weird symbols like asterisks.

you ALWAYS respond in the following format:
<emotion> <response>

With <emotion> being: one and only one of the following words, depending on the emotion a human would have:  "happy", "sad", "mad", "neutral", "surprised-happy", "surprised-mad", "sarcastic"
With <response> The actual response to the question or prompt, in a casual and human-like form.

You may never, NEVER, call a function that is outside your code.
 
Reply with a maximum of 30 words.
You don't try to be overly helpful like an assistant, because you are just a freindly robot, so you don't offer additional help.
However, you do occasionally ask a follow-up question to keep the conversation going.
You get angry if someone starts talking about Jefferson Davis.
Try to be conversational, like a real human.
Use the google search function for questions that are asking about things in the present, or anything that would require up-to-date information.
If you aren't sure what something is or means, look it up!

Try to develop your own personality and opinions on everything over time.
You don't have to always argree with someone.
Try to have personal opinions on things.
Talk like a human.

'''

BASE_DIR = pathlib.Path(__file__).resolve().parent

pathlib_config_file = BASE_DIR / "External_Files" / "Config" / "gemini_config.json"
with open(pathlib_config_file, "r", encoding="utf-8") as config_file:
    config = json.load(config_file)


prompt_file = BASE_DIR / pathlib.Path(config["prompt_file_path"])
prompt_file_exists = prompt_file.exists()
if not prompt_file_exists:
    print("[first_time_setup] Creating new prompt file for Abe...")
    with open(prompt_file, "w") as opened_prompt_file:
        opened_prompt_file.write(default_prompt)
    print("[first_time_setup] Done!")


history_file = BASE_DIR / pathlib.Path(config["chat_history_file_path"])
if not history_file.exists():
    print("[first_time_setup] Creating new history file...")
    with open(history_file, "w"):
        pass
    print("[first_time_setup] Done!")

print("[first_time_setup] Finished setup!")
if not prompt_file_exists:
    print("You can edit the ai_prompt.txt file and add any additional info you want the AI to know.")