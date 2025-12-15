import queue
import threading

class GUIIO:
    """
    Captures print() and input() from the game and routes them to the GUI.
    """

    def __init__(self):
        self.output_callback = None
        self.input_queue = queue.Queue()
        self.wait_event = threading.Event()

    def set_output_callback(self, func):
        self.output_callback = func

    def write(self, text):
        if self.output_callback:
            self.output_callback(text)

    def input(self, prompt=""):
        # prints the prompt first
        if prompt and self.output_callback:
            self.output_callback(prompt)

        #waits until GUI sends input
        self.wait_event.clear()
        self.wait_event.wait()
        return self.input_queue.get()

    def send_input_from_gui(self, text):
        self.input_queue.put(text)
        self.wait_event.set()