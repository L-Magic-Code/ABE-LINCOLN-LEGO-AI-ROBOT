from google import genai
from google.genai import types #type: ignore
import json
from PIL import Image
import cv2
import pathlib

class AI:
    def __init__(self):
        """
        Sets up the genai client, api key, and chat.
        """
        with open("AbeOS 1.0/External_Files/Config/gemini_config.json", "r") as config_file:
            self.config_str = config_file.read()
        self.config = json.loads(self.config_str)
        with open(self.config["path_to_gemini_api_key"]) as open_file:
            self.client = genai.Client(api_key=open_file.read())

        raw_prompt_file = self.config["prompt_file_path"]
        base_direcotry = pathlib.Path(__file__).resolve().parent

        file = base_direcotry / raw_prompt_file

        self.chat = self.client.chats.create(
            model=self.config["gemini_model"],
            config=types.GenerateContentConfig(
                system_instruction=self.get_file_text(file),
                temperature=.5)
        )


        self.possible_emotions = ["happy", "sad", "neutral", "surprised", "mad", "scared"]
        print("[gemini_functions] set up the client and Abe's chat!")

    def get_file_text(self, file) -> str:
        """
        Reads the "file" attribute and returns the file's text.
        """
        with open(file, "r") as open_file:
            self.file_text = open_file.read()
        return self.file_text
    
    def load_history(self):
        """
        Sends all conversation history to the AI.
        """
        self.history = self.get_file_text(self.config["chat_history_file_path"])
        if  self.history != '':
            self.chat.send_message("Our conversation so far has been the following: \n" + self.history)
        else:
            print("[gemini_functions] Conversation history empty. Skipping history loading.")

    def send_ai_prompt(self):
        self.ai_prompt = self.get_file_text(self.config["prompt_file_path"])

        if self.ai_prompt == '':
            raise SyntaxError("No AI Prompt! Please add a prompt for Abe in the file ai_prompt.txt!")
        else:
            self.chat.send_message(self.ai_prompt)

    def get_response(self, prompt: str=None, image=None, trigger_word='') -> tuple[str, str, str]:
        """
        Returns a variables in this EXACT order: emotion, function, response
        
        Takes a str prompt that consists of the user's prompt.
        
        Also takes an optional image that WILL be sent to gemini.
        """

        if prompt == None or prompt == '':
            raise SyntaxError("Prompt was None, or empty!")

        self.prompt = str(prompt)
        
        if image is not None:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self.pil_image = Image.fromarray(image)
            if trigger_word != '':
                print(f"[gemini_functions] Sending image to Gemini along with prompt! Trigger by: {trigger_word}!")
            else:
                print("[gemini_functions] Sending image to Gemini along with prompt!")
            self.response = self.chat.send_message([self.pil_image, self.prompt])
        else:
            self.response = self.chat.send_message(self.prompt)

        self.text = self.response.text.split(None, 2)[2]
        self.generated_emotion = self.response.text.split()[0]
        self.function = self.response.text.split()[1]
        if not self.generated_emotion.lower() in self.possible_emotions:
            self.generated_emotion = "neutral"
        return  self.generated_emotion, self.function, self.text
    

if __name__ == '__main__':
    ai = AI()
    while True:
        myinput = input("You: ")
        _, _, respo = ai.get_response(myinput)
        print(respo)
    