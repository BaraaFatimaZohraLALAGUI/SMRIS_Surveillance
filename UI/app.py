import customtkinter as ctk 
import numpy as np
from PIL import Image 
import cv2
from utils.constants import *
from UI.tab_view import TabView


class App (ctk.CTk):

    def __init__ (self, app_name="SMRIS AI Surveillance"):
        super ().__init__ ()
        self.title (app_name)
        self._state_before_windows_set_titlebar_color = 'zoomed'
        self.minsize(1200, 800)
        self.bind('<Escape>', lambda e: self.quit()) 
        self.tabview = None

    def run (self):
        self.ui_setup ()
        self.tabview.open_camera ()
        self.mainloop ()
        self.cleanup ()

    def ui_setup (self):

        self.parent_frame = ctk.CTkFrame (self, fg_color='transparent')
        # self.parent_frame.pack (expand=True, fill='both', pady=20, padx = 60)
        self.parent_frame.place (relx=0.02, rely=0.05, relwidth=.96, relheight=.9)

        logo = cv2.cvtColor(cv2.imread ("UI/gfx/smris_surveillance_logo.png", -1), cv2.COLOR_BGR2RGBA) 
        logo = ctk.CTkImage (dark_image=Image.fromarray(logo), size=(np.array (logo.shape[:2][::-1]) * .32).tolist ())

        self.logo_frame = ctk.CTkFrame (self.parent_frame, fg_color='transparent')
        # self.logo_frame.pack (side='top', expand=False, fill='x', pady=0, ipady=0)
        self.logo_frame.place (x=0, y=0, relwidth=1, relheight=.06)

        self.logo_label = ctk.CTkLabel (self.logo_frame, text='', image=logo, fg_color='transparent', bg_color='transparent')
        self.logo_label.pack (side='left', expand=False, padx=0, pady=0, ipady=0)

        # tabview to navigate through tabs
        self.tabview = TabView(self.parent_frame, segmented_button_selected_color=VIOLET_LIGHT, segmented_button_selected_hover_color=VIOLET_LIGHT)
        # self.tabview.pack(expand=True, fill='both')
        self.tabview.place (relx=0, rely=.06, relwidth=1, relheight=.94)

        self.tabview._segmented_button.configure(font=('Calibri', 20))
        # self.tabview._segmented_button.grid(sticky='nw')

        
    def cleanup (self):
        self.tabview.input_vcap.release ()

