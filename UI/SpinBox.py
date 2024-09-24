from typing import Callable, Union
import customtkinter as ctk

class IntSpinbox(ctk.CTkFrame):
    def __init__(self, *args,
                 width: int = 50,
                 height: int = 10,
                 step_size: int = 1,
                 command: Callable = None,
                 button_color='green',
                 font = ('Calibri', 14),
                 button_hover_color = 'white',
                 value : int = 200,
                 min_val = 0,
                 max_val=500,
                 text_font = ('Calibri', 16),
                 **kwargs):
        super().__init__(*args, width=width, height=0, **kwargs)

        self.min_val = min_val
        self.max_val = max_val

        self.step_size = step_size
        self.command = command

        self.configure(fg_color=("grey78"))  # set frame color

        self.grid_columnconfigure(0, weight=1)  # Entry expands 
        self.grid_columnconfigure(1, weight=0)  # Buttons don't expand
        self.grid_rowconfigure(0, weight=0) 

        self.entry = ctk.CTkEntry(self, width=width-(2*10), height=10-6, border_width=0, font=text_font)
        self.entry.grid(row=0, column=0, columnspan=1, padx=3, pady=1, sticky="ew")

        self.buttons_frame = ctk.CTkFrame (self, fg_color='transparent')
        self.buttons_frame.grid (row=0, column=1, padx=(1, 4), pady=1, sticky="news")
        self.add_button = ctk.CTkLabel(self.buttons_frame, text="+", corner_radius=1, width=10, height=5, fg_color=button_color, font=font)
        self.add_button.pack(expand=True, fill='both')
        self.add_button.bind('<Button-1>', self.add_button_callback)
        self.subtract_button = ctk.CTkLabel(self.buttons_frame, text="-", corner_radius=1,  width=10, height=5, fg_color=button_color, font=font)
        self.subtract_button.pack(expand=True, fill='both')
        self.subtract_button.bind('<Button-1>', self.subtract_button_callback)

        # default value
        self.entry.insert(value, str (value))

    def add_button_callback(self, event):
        if self.command is not None:
            self.command()
        try:
            value = int(self.entry.get()) + self.step_size
            if value > self.max_val:
                return 
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
        except ValueError:
            return

    def subtract_button_callback(self, event):
        if self.command is not None:
            self.command()
        try:
            value = int(self.entry.get()) - self.step_size
            if value < self.min_val:
                return 
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
        except ValueError:
            return

    def get(self) -> Union[int, None]:
        try:
            return int(self.entry.get())
        except ValueError:
            return None

    def set(self, value: int):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(int(value)))