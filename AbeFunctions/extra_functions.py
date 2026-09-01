import time
import threading

def _cool_print(text, print_time, delay):
    r"""
    Prints 'text' from left to right over 'print_time'.

    Not designed for \r or \n.
    """
    time.sleep(delay)
    if text == '':
        print("")
        return
    
    sleep_time = print_time / len(text)
    for letter in text:
        print(letter, end='')
        time.sleep(sleep_time)
    print()

def cool_print(text : str, print_time : int=1, thread : bool=False, delay : float=0):
    r"""
    Prints 'text' from left to right over 'print_time'.
    If thread is True, it will start it as a thread, otherwise it will block.

    Not designed for \r or \n.
    """
    if thread:
        threading.Thread(target=_cool_print, args=[text, print_time, delay]).start()
    else:
        _cool_print(text=text, print_time=print_time, delay=delay)

def print_red(text):
    print("\033[0;31m" + str(text) + "\033[0m")

if __name__ == '__main__':
    print_red("OH NO!")
    cool_print("Hello World! This is a code that was made for Abe!", 3)

class function_calling_handeler:
    def __init__(self, ev3_function_handeler, vision_function_handeler):
        self.ev3_function_handeler = ev3_function_handeler
        self.vision_function_handeler = vision_function_handeler
        self.vision_functions = ['look_at_users_hand', 'look_at_users_face']
        self.ev3_functions = ['grab_something', 'wave', 'drop_item_in_hand',"open_chest", "close_chest"]


    def complete_function(self, function : str=''):
        if function == 'no_function_needed':
            return
        elif function in self.ev3_functions:
            self.ev3_function_handeler.complete_mindstorms_function(function)
        elif function in self.vision_functions:
            self.vision_function_handeler.complete_vision_function(function)
        else:
            print_red(f"[extra_functions] [ERROR] Unknown function: {function}")