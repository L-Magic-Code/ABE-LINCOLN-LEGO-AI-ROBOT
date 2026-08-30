import time
import threading

def _cool_print(text, print_time):
    r"""
    Prints 'text' from left to right over 'print_time'.

    Not designed for \r or \n.
    """
    if text == '':
        print("")
        return
    
    sleep_time = print_time / len(text)
    for letter in text:
        print(letter, end='')
        time.sleep(sleep_time)
    print()

def cool_print(text : str, print_time : int=1, thread : bool=False):
    r"""
    Prints 'text' from left to right over 'print_time'.
    If thread is True, it will start it as a thread, otherwise it will block.

    Not designed for \r or \n.
    """
    if thread:
        threading.Thread(target=_cool_print, args=[text, print_time]).start()
    else:
        _cool_print(text=text, print_time=print_time)

def print_red(text):
    print("\033[0;31m" + str(text) + "\033[0m")

if __name__ == '__main__':
    print_red("OH NO!")
    cool_print("Hello World! This is a code that was made for Abe!", 3)
    