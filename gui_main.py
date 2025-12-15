import threading
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import requests
from io import BytesIO

from main import TwentyQuestionsGame
import gui_io

class GameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pokémon 20 Questions")
        self.io = gui_io.GUIIO()
        self.io.set_output_callback(self.gui_print)

        self.text_box = None
        self.button_frame = None
        self.yes_button = None
        self.no_button = None
        self.image_label = None
        self.game_thread = None
        self.game = None

        self.build_start_screen()

    #prints console text to gui
    def gui_print(self, text):
        if self.text_box:
            self.text_box.insert(tk.END, text + "\n")
            self.text_box.see(tk.END)

    #start screen
    def build_start_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = tk.Frame(self.root)
        frame.pack(expand=True)

        tk.Label(frame, text="Pokémon 20 Questions", font=("Arial", 24)).pack(pady=20)

        tk.Button(frame, text="Start", font=("Arial", 18),
                  command=self.begin_game_screen).pack(pady=10)

        tk.Button(frame, text="Stats", font=("Arial", 18),
                  command=self.show_stats_screen).pack(pady=10)

    #begin game screen
    def begin_game_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.text_box = scrolledtext.ScrolledText(self.root, width=80, height=25, font=("Consolas", 12))
        self.text_box.pack(pady=10)

        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack()

        self.yes_button = tk.Button(self.button_frame, text="YES", font=("Arial", 16),
                                    command=lambda: self.send_input("yes"))
        self.no_button = tk.Button(self.button_frame, text="NO", font=("Arial", 16),
                                   command=lambda: self.send_input("no"))

        self.yes_button.pack(side="left", padx=20)
        self.no_button.pack(side="left", padx=20)

        #start game thread
        self.game_thread = threading.Thread(target=self.run_game)
        self.game_thread.start()

    #shows the stats screen
    def show_stats_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.text_box = scrolledtext.ScrolledText(self.root, width=80, height=25, font=("Consolas", 12))
        self.text_box.pack(pady=10)

        back_btn = tk.Button(self.root, text="Back", font=("Arial", 16),
                         command=self.build_start_screen)
        back_btn.pack(pady=10)

    # --- REDIRECT PRINT FOR THIS ONE FUNCTION ---
        import builtins
        real_print = builtins.print

        def gui_print(*args, **kwargs):
            text = " ".join(str(a) for a in args)
            self.io.write(text)

        builtins.print = gui_print

        try:
            temp_game = TwentyQuestionsGame()
            temp_game.show_stats()
            temp_game.db.close()
        finally:
        # Restore real print when done
            builtins.print = real_print

    #runs the game
    def run_game(self):
        self.game = TwentyQuestionsGame()

        #patches to show_pokemon_details to show images
        original_show = self.game._show_pokemon_details
        def patched_show(pokemon):
            original_show(pokemon)
            if pokemon.get("Sprite_Default"):
                self.show_image(pokemon["Sprite_Default"])
        self.game._show_pokemon_details = patched_show

        #redirects to print/input
        __builtins__.print = self.io.write
        __builtins__.input = self.io.input

        try:
            self.game.start()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", str(e))

        #calls after the game ends
        self.ask_restart()

    #sends the input from the gui buttons
    def send_input(self, text):
        self.io.send_input_from_gui(text)

    # restarts the prompt
    def ask_restart(self):
        def build():
            for widget in self.root.winfo_children():
                widget.destroy()

            label = tk.Label(self.root, text="Restart?", font=("Arial", 22))
            label.pack(pady=20)

            yes_btn = tk.Button(self.root, text="YES", font=("Arial", 18),
                                command=self.build_start_screen)
            no_btn = tk.Button(self.root, text="NO", font=("Arial", 18),
                               command=self.root.quit)

            yes_btn.pack(pady=10)
            no_btn.pack(pady=10)

        self.root.after(10, build)

    # shows the image
    def show_image(self, url):
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            img = img.resize((250, 250))
            img_tk = ImageTk.PhotoImage(img)

            if self.image_label is None:
                self.image_label = tk.Label(self.root, image=img_tk)
                self.image_label.image = img_tk
                self.image_label.pack(pady=10)
            else:
                self.image_label.configure(image=img_tk)
                self.image_label.image = img_tk
        except:
            pass

#runs gui
if __name__ == "__main__":
    root = tk.Tk()
    gui = GameGUI(root)
    root.mainloop()