from typing import Callable, Union
import customtkinter as ctk

class IntSpinbox(ctk.CTkFrame):
    def __init__(self, *args,
                 width: int = 100,
                 height: int = 32,
                 step_size: int = 1,
                 command: Callable = None,
                 button_color='green',
                 font = ('Calibri', 12),
                 button_hover_color = 'white',
                 value : int = 200,
                 min_val = 0,
                 max_val=500,
                 **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

        self.min_val = min_val
        self.max_val = max_val

        self.step_size = step_size
        self.command = command

        self.configure(fg_color=("gray78", "gray28"))  # set frame color

        self.grid_columnconfigure(0, weight=1)  # Entry expands 
        self.grid_columnconfigure(1, weight=0)  # Buttons don't expand

        self.entry = ctk.CTkEntry(self, width=width-(2*height), height=height-6, border_width=0, font=('Calibri', 18))
        self.entry.grid(row=0, column=0, columnspan=1, padx=3, pady=3, sticky="news")

        self.buttons_frame = ctk.CTkFrame (self, fg_color='transparent')
        self.buttons_frame.grid (row=0, column=1, padx=(1, 4), pady=3)
        self.add_button = ctk.CTkButton(self.buttons_frame, text="+", corner_radius=5, width=30, height=5, command=self.add_button_callback, fg_color=button_color, font=font, border_width=0, hover_color=button_hover_color)
        self.add_button.pack(expand=False, fill='x')
        self.subtract_button = ctk.CTkButton(self.buttons_frame, text="-", corner_radius=5,  width=30, height=5, command=self.subtract_button_callback, fg_color=button_color, font=font, border_width=0, hover_color=button_hover_color)
        self.subtract_button.pack(expand=False, fill='x')

        # default value
        self.entry.insert(value, str (value))

    def add_button_callback(self):
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

    def subtract_button_callback(self):
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