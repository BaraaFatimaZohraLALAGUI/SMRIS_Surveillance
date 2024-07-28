import datetime
import customtkinter as ctk 
import numpy as np
from PIL import Image 
import cv2
from UI.SpinBox import IntSpinbox
from db.db_manager import insert_record
from utils.cam_functions import get_vcap, setup_output_stream
from utils.yolo_api import detect, load_model 
from CTkColorPicker import *




class App (ctk.CTk):

    STANDARD_FONT = ("Calibri", 18) 
    FRAME_SCALE = .3
    FRAME_WIDTH, FRAME_HEIGHT = (640, 480) 
    FRAME_SIZE = (FRAME_WIDTH, FRAME_HEIGHT)
    BLACK = '#2B2B2B'
    VIOLET_DARK = '#474554'
    VIOLET_LIGHT = '#ACA9BB'
    GREEN_DARK = '#26473D'
    GREEN_LIGHT = '#55786C'    

    def __init__ (self, app_name="SMRIS AI Surveillance"):
        super ().__init__ ()
        self.title (app_name)
        self._state_before_windows_set_titlebar_color = 'zoomed'
        self.bind('<Escape>', lambda e: self.quit()) 

        self.channels = ['1', '2', '3', '4']
        self.models = ['YOLOv9 Tiny', 'YOLOv10 Nano', 'YOLOv10 Small', 'YOLOv10 Medium', 'YOLOv10 Big', 'YOLOv10 Large', 'YOLOv10 Extra Large']
        

        self.selected_channel = ctk.StringVar (value=self.channels[3])
        
        self.selected_model = ctk.StringVar (value=self.models[0])
        self.detection_enabled = ctk.BooleanVar (value=False)

        self.model = load_model('YOLOv9 Tiny')

        self.detection_threshold = .25
        self.current_rec_frame_count = 0

        self.RECT_COLOR = (255, 255, 0)

        self.camera_ip_address = ctk.StringVar (value="10.1.67.111")
        self.input_vcap = get_vcap (self.camera_ip_address.get (), channel = 1) # int (self.selected_channel.get ())
        self.out_cap = None

        self.recording_behavior = ctk.StringVar (value="Recording off") # 'Recording off', 'Continuous recording', 'Only on detection'
        self.recording_storage_path = 'captures_out2'

        ## Background Substratction
        self.bg_substraction_methods = ['Mixture-of-Gaussian - MoG', 'MoG2']
        self.bgSub_history_states = 200
        self.background_substractor = cv2.bgsegm.createBackgroundSubtractorMOG(history=self.bgSub_history_states, nmixtures=3, backgroundRatio=.95, noiseSigma=10)
        self.bgSub_MOG_nGaussians = 5
        self.bgSub_MOG_bgRatio = .85

    def run (self):
        self.ui_setup ()
        self.open_camera ()
        self.mainloop ()
        self.cleanup ()

    def ui_setup (self):
        self.parent_frame = ctk.CTkFrame (self, fg_color='transparent')
        self.parent_frame.pack (expand=True, fill='both', pady=20, padx = 60)


        logo = cv2.cvtColor(cv2.imread ("UI/gfx/smris_surveillance_logo.png", -1), cv2.COLOR_BGR2RGBA) 
        logo = ctk.CTkImage (dark_image=Image.fromarray(logo), size=(np.array (logo.shape[:2][::-1]) * .4).tolist ())

        self.logo_frame = ctk.CTkFrame (self.parent_frame, fg_color='transparent')
        self.logo_frame.pack (side='top', expand=False, fill='x', pady=0, ipady=0)
        self.logo_label = ctk.CTkLabel (self.logo_frame, text='', image=logo, fg_color='transparent', bg_color='transparent')
        self.logo_label.pack (side='left', expand=False, padx=0, pady=0, ipady=0)

        
        self.camera_frame = ctk.CTkFrame (self.parent_frame, corner_radius=10) 
        self.camera_frame.pack (side='left', expand=False, fill='y', pady=10, padx=20)

        self.cam_ip_frame = ctk.CTkFrame (self.camera_frame)
        self.cam_ip_frame.pack (expand=False, fill='x', pady=20, padx=40)

        self.ip_entry_field = ctk.CTkEntry (self.cam_ip_frame, textvariable=self.camera_ip_address, corner_radius = 0, font=self.STANDARD_FONT, border_color= self.VIOLET_DARK)
        self.ip_entry_field.pack (side='left', expand=True, fill='x')

        self.channel_label = ctk.CTkLabel (self.camera_frame, text='Channel ' + self.selected_channel.get (), font=('Calibri', 24, 'bold')) 
        self.channel_label.pack (side='top')

        self.cam_connect_button = ctk.CTkButton (self.cam_ip_frame, text="Connect", command = self.channel_select, fg_color= self.VIOLET_DARK, hover_color= self.VIOLET_LIGHT ,corner_radius = 0, font=self.STANDARD_FONT, width=200)
        self.cam_connect_button.pack (side='right', expand=False, fill='both')

        self.cam_view = ctk.CTkLabel (self.camera_frame, text='', corner_radius=15) 
        self.cam_view.pack(expand=False, fill='x', pady=15, padx=40, side='top') 

        # Channel selection buttons 
        self.channel_selection_frame = ctk.CTkFrame (self.camera_frame, fg_color='transparent')
        self.channel_selection_frame.pack ( padx=180, pady=10)

        self.channel_selection_frame.columnconfigure (0, weight=1)
        self.channel_selection_frame.columnconfigure (1, weight=1)
        self.channel_selection_frame.rowconfigure (0, weight=1)
        self.channel_selection_frame.rowconfigure (1, weight=1)

        top_left_icon = cv2.cvtColor(cv2.imread ("UI/gfx/TOP_LEFT.png", -1)[:-180, 100:, :], cv2.COLOR_BGR2RGBA) 
        top_left_icon = ctk.CTkImage (dark_image=Image.fromarray(top_left_icon), size=(35, 35))

        top_right_icon = cv2.cvtColor(cv2.imread ("UI/gfx/TOP_RIGHT.png", -1)[:-180, :-100, :], cv2.COLOR_BGR2RGBA) 
        top_right_icon = ctk.CTkImage (dark_image=Image.fromarray(top_right_icon), size=(35, 35))

        bottom_left_icon = cv2.cvtColor(cv2.imread ("UI/gfx/BOTTOM_LEFT.png", -1)[180:, 100:, :], cv2.COLOR_BGR2RGBA) 
        bottom_left_icon = ctk.CTkImage (dark_image=Image.fromarray(bottom_left_icon), size=(35, 35))

        bottom_right_icon = cv2.cvtColor(cv2.imread ("UI/gfx/BOTTOM_RIGHT.png", -1)[180:, :-100, :], cv2.COLOR_BGR2RGBA) 
        bottom_right_icon = ctk.CTkImage (dark_image=Image.fromarray(bottom_right_icon), size=(35, 35))

        self.channel_top_left = ctk.CTkButton (master=self.channel_selection_frame, image=top_left_icon, text="", command=lambda : self.channel_select (4), font=self.STANDARD_FONT, fg_color='transparent', bg_color='transparent', border_color=self.VIOLET_DARK, hover_color = self.VIOLET_LIGHT ,border_width=2, corner_radius=10)
        self.channel_top_left.grid (row=0, column=0, sticky='news', padx=5, pady=5)

        self.channel_top_right = ctk.CTkButton (self.channel_selection_frame, image=top_right_icon, text="", command=lambda : self.channel_select (1), font=self.STANDARD_FONT, fg_color='transparent', bg_color='transparent', border_color=self.VIOLET_DARK, hover_color = self.VIOLET_LIGHT ,border_width=2, corner_radius=10)
        self.channel_top_right.grid (row=0, column=1, sticky='news', padx=5, pady=5)

        self.channel_bottom_left = ctk.CTkButton (self.channel_selection_frame, image=bottom_left_icon, text="", command=lambda : self.channel_select (3), font=self.STANDARD_FONT, fg_color='transparent', bg_color='transparent', border_color=self.VIOLET_DARK, hover_color = self.VIOLET_LIGHT, border_width=2, corner_radius=10)
        self.channel_bottom_left.grid (row=1, column=0, sticky='news', padx=5, pady=5)

        self.channel_bottom_right = ctk.CTkButton (self.channel_selection_frame, image=bottom_right_icon, text="", command=lambda : self.channel_select (2), font=self.STANDARD_FONT,  fg_color='transparent', bg_color='transparent', border_color=self.VIOLET_DARK, hover_color = self.VIOLET_LIGHT, border_width=2, corner_radius=10)
        self.channel_bottom_right.grid (row=1, column=1, sticky='news', padx=5, pady=5)

        ### Detection control 
        self.detection_frame = ctk.CTkFrame (self.parent_frame, bg_color='transparent', corner_radius=10)
        self.detection_frame.pack (side='right', pady=10, padx=20, expand=True, fill='x')

        self.detection_frame.columnconfigure (0, weight=1)
        self.detection_frame.columnconfigure (1, weight=1)
        self.detection_frame.columnconfigure (2, weight=1)
        self.detection_frame.rowconfigure (0, weight=1)
        self.detection_frame.rowconfigure (1, weight=1)
        self.detection_frame.rowconfigure (2, weight=1)
        self.detection_frame.rowconfigure (3, weight=1)
        self.detection_frame.rowconfigure (4, weight=1)
        self.detection_frame.rowconfigure (5, weight=1)

        self.detection_toggle = ctk.CTkSwitch(self.detection_frame, text='Enable detection', variable=self.detection_enabled, switch_width=50, command=self.toggle_detection, font=self.STANDARD_FONT, fg_color= self.VIOLET_DARK, progress_color= self.VIOLET_LIGHT) 
        self.detection_toggle.grid (row=0, column = 0, pady= 20, padx = 40, columnspan=1, sticky='w')

        self.detection_frame_color_button = ctk.CTkButton(self.detection_frame, text="Detection frame color", command=self.color_picker, font=self.STANDARD_FONT, width=130, height=40, corner_radius=20, border_color=self.bgr_to_hex(self.RECT_COLOR),  border_width=1, fg_color= 'transparent')
        self.detection_frame_color_button.grid(row=0, column=1, pady=20, padx=30, columnspan=2, sticky='ew')
        
        # Background substraction
        bgSub_frame = ctk.CTkFrame (self.detection_frame, fg_color='transparent', border_color="#454545", border_width=1)
        bgSub_frame.grid (row=1, column=0, columnspan=3, sticky='news', padx=30, pady=10)
        bgSub_frame.columnconfigure (0, weight=1)
        bgSub_frame.columnconfigure (1, weight=1)
        bgSub_frame.rowconfigure (0, weight=1)
        bgSub_frame.rowconfigure (1, weight=1)
        bgSub_frame.rowconfigure (2, weight=1)

        self.bgSub_toggle_var = ctk.BooleanVar (value=True)
        self.bgSub_toggle = ctk.CTkSwitch(bgSub_frame, text='Enable background substraction', switch_width=50, command=self.toggle_bgSub, font=self.STANDARD_FONT, fg_color= self.VIOLET_DARK, progress_color= self.VIOLET_LIGHT, variable=self.bgSub_toggle_var) 
        self.bgSub_toggle.grid (row=0, column = 0, pady= 10, padx = 10, columnspan=2, sticky='w')

        self.bgSub_label = ctk.CTkLabel (bgSub_frame, text= 'Select a background substraction method', font=self.STANDARD_FONT)
        self.bgSub_label.grid (row=1, column=0, pady=10, padx=10, sticky='w')

        self.bgSub_combo = ctk.CTkComboBox (bgSub_frame, values=self.bg_substraction_methods, font=self.STANDARD_FONT, width=450, command=self.select_bgSubstractor, dropdown_font=self.STANDARD_FONT)
        self.bgSub_combo.grid (row=1, column=1, padx=20, pady=10, sticky='e')

        self.bgSub_view = ctk.CTkLabel (bgSub_frame, text='', corner_radius=15) 
        self.bgSub_view.grid (row=2, column = 1, pady= 10, padx = 5, sticky='news')

        # BG MOG PARAMETERS 
        self.MOG_params_frame = ctk.CTkFrame (bgSub_frame)
        self.MOG_params_frame.grid (row=2, column = 0, pady= 10, padx = 5, sticky='news')

        self.MOG_params_frame.columnconfigure (0, weight=1)
        self.MOG_params_frame.columnconfigure (1, weight=1)
        self.MOG_params_frame.rowconfigure ((0, 1, 2), weight=1)

        history_label = ctk.CTkLabel (self.MOG_params_frame, text= "Number of history entries", font=self.STANDARD_FONT)
        history_label.grid (row=0, column=0, padx=20, pady=5, sticky='w')
        self.history_spinbox = IntSpinbox(self.MOG_params_frame, width=150, step_size=1, value=self.bgSub_history_states, button_color=self.VIOLET_DARK, button_hover_color=self.VIOLET_LIGHT, command=self.history_spinbox_callback)
        self.history_spinbox.grid(row=0, column=1, padx=20, pady=5, sticky='ew')

        nGaussian_mixtures = ctk.CTkLabel (self.MOG_params_frame, text= "Number of Gaussian mixtures", font=self.STANDARD_FONT)
        nGaussian_mixtures.grid (row=1, column=0, padx=20, pady=5, sticky='w')
        self.nGaussian_mixtures_spinbox = IntSpinbox(self.MOG_params_frame, width=150, step_size=1, value=self.bgSub_MOG_nGaussians, button_color=self.VIOLET_DARK, button_hover_color=self.VIOLET_LIGHT, command=self.nGaussians_spinbox_callback)
        self.nGaussian_mixtures_spinbox.grid(row=1, column=1, padx=20, pady=5, sticky='ew')

        bgSub_bgRatio_label = ctk.CTkLabel (self.MOG_params_frame, text= "Background ratio", font=self.STANDARD_FONT)
        bgSub_bgRatio_label.grid (row=2, column=0, padx=20, pady=5, sticky='w')

        self.bgSub_bgRatio_slider = ctk.CTkSlider(master=self.MOG_params_frame, from_=0, to=1, command= self.bgRatio_slider_callback, width = 150, button_color = '#FFFFFF', button_hover_color='#FFFFFF', progress_color= self.VIOLET_LIGHT) 
        self.bgSub_bgRatio_slider.set (self.bgSub_MOG_bgRatio)
        self.bgSub_bgRatio_slider.grid (row=2, column = 1, padx=5, pady=5, sticky = 'ew')


        ## Model selection 
        self.model_select_frame = ctk.CTkFrame (self.detection_frame, fg_color='transparent', border_color="#454545", border_width=1)
        self.model_select_frame.grid (row=2, column=0, columnspan=3, sticky='we', padx=30, pady=10)

        self.model_select_frame.columnconfigure (0, weight=1)
        self.model_select_frame.columnconfigure (1, weight=1)
        self.model_select_frame.rowconfigure (0, weight=1)

        self.model_select_label = ctk.CTkLabel (self.model_select_frame, text="Select an inference model", font=self.STANDARD_FONT)
        self.model_select_label.grid (row=0, column=0, pady=10, padx=10, sticky='w')

        self.model_combo = ctk.CTkComboBox (self.model_select_frame, values=self.models, variable=self.selected_model, command = lambda event: self.model_select (), width=450)
        self.model_combo.grid (row=0, column=1, padx=20, pady=10, sticky='e')

        ## Threshold adjusments
        self.threshold_frame = ctk.CTkFrame(self.detection_frame, bg_color = 'transparent', corner_radius = 20, border_color = "#3B3B3B", border_width= 1)
        self.threshold_frame.grid(row=3, column=0, columnspan=3, pady=5, padx=30, ipady=10, sticky='ew')
        self.threshold_frame.columnconfigure (0, weight=1)
        self.threshold_frame.rowconfigure (0, weight=1)
        self.threshold_frame.rowconfigure (1, weight=1)

        self.detection_threshold_slider = ctk.CTkSlider(master=self.threshold_frame, from_=0.2, to=.95, command= self.detection_threshold_adjust, width = 400, button_color = '#FFFFFF', button_hover_color='#FFFFFF', progress_color= self.VIOLET_LIGHT) 
        self.detection_threshold_slider.set (self.detection_threshold)
        self.detection_threshold_slider.grid (row=0, column = 0, padx=20, pady=0, sticky = 'ew')

        self.detection_threshold_value = ctk.CTkLabel (self.threshold_frame, text=f"{self.detection_threshold:.3f}", font=self.STANDARD_FONT)
        self.detection_threshold_value.grid (row=0, column = 2, padx=20, pady=0, sticky='w')

        self.detection_threshold_label = ctk.CTkLabel (self.threshold_frame, text="Detection Threshold", font=self.STANDARD_FONT)
        self.detection_threshold_label.grid (row=2, column = 0, padx=10, pady=0)

        ## Recording behavior
        self.recording_segmented_buttons = ctk.CTkSegmentedButton (self.detection_frame, selected_color=self.VIOLET_LIGHT, border_width=1, font=self.STANDARD_FONT, values=['Recording off', 'Continuous recording', 'Only on detection'], unselected_color="#333333", height=40, selected_hover_color=self.VIOLET_LIGHT, variable=self.recording_behavior)
        self.recording_segmented_buttons.grid (row=4, column = 0, padx=30, pady=20, columnspan=3, sticky='nsew')

        ## Storage folder chooser
        self.folder_chooser_frame = ctk.CTkFrame(self.detection_frame, bg_color = 'transparent', corner_radius = 20, border_color = "#3B3B3B", border_width= 1, height=150)
        self.folder_chooser_frame.grid (row=5, column = 0, padx=30, pady=20, columnspan=3, sticky='nsew')

        self.folder_chooser_button = ctk.CTkButton (self.folder_chooser_frame, text='Choose a storage directory', command=self.select_folder, font=self.STANDARD_FONT, width=130, height=40, corner_radius=20, border_color=self.VIOLET_DARK, hover_color=self.VIOLET_LIGHT,border_width=1, fg_color= self.VIOLET_DARK)
        self.folder_chooser_button.pack (side='left', pady=20, padx= 20)

        self.storage_path_label = ctk.CTkLabel (self.folder_chooser_frame, text=self.recording_storage_path, font=self.STANDARD_FONT)
        self.storage_path_label.pack (side='left')


    def select_folder(self):
        folder_path = ctk.filedialog.askdirectory()
        if folder_path == "": return
        self.storage_path_label.configure (text=folder_path.replace ('/', '\\'))

    def toggle_bgSub (self):
        if not self.bgSub_toggle.get ():
            self.bgSub_view.grid_remove ()
        else:
            self.bgSub_view.grid ()

    def bgRatio_slider_callback (self, event):
        self.bgSub_MOG_bgRatio = self.bgSub_bgRatio_slider.get ()
        self.select_bgSubstractor (None)

    def history_spinbox_callback (self):
        self.bgSub_history_states = int (self.history_spinbox.get ())
        self.select_bgSubstractor (None)

    def nGaussians_spinbox_callback (self):
        self.bgSub_MOG_nGaussians = int (self.nGaussian_mixtures_spinbox.get ())
        self.select_bgSubstractor (None)

    def channel_select (self, channel=1):
        self.selected_channel.set (channel)
        self.channel_label.configure (text = f"Channel {channel}")
        self.input_vcap = get_vcap (self.camera_ip_address.get (), channel = channel) 
        if channel == 4:
            self.channel_top_left.configure (fg_color=self.VIOLET_LIGHT)
            self.channel_top_right.configure (fg_color="transparent")
            self.channel_bottom_left.configure (fg_color="transparent")
            self.channel_bottom_right.configure (fg_color="transparent")
        elif channel == 1:
            self.channel_top_left.configure (fg_color="transparent")
            self.channel_top_right.configure (fg_color=self.VIOLET_LIGHT)
            self.channel_bottom_left.configure (fg_color="transparent")
            self.channel_bottom_right.configure (fg_color="transparent")
        elif channel == 3:
            self.channel_top_left.configure (fg_color="transparent")
            self.channel_top_right.configure (fg_color="transparent")
            self.channel_bottom_left.configure (fg_color=self.VIOLET_LIGHT)
            self.channel_bottom_right.configure (fg_color="transparent")
        elif channel == 2:
            self.channel_top_left.configure (fg_color="transparent")
            self.channel_top_right.configure (fg_color="transparent")
            self.channel_bottom_left.configure (fg_color="transparent")
            self.channel_bottom_right.configure (fg_color=self.VIOLET_LIGHT)


    def model_select (self):
        self.model = load_model(self.selected_model.get ())

    def select_bgSubstractor (self, event):
        if self.bgSub_combo.get () == "Mixture-of-Gaussian - MoG":
             self.background_substractor = cv2.bgsegm.createBackgroundSubtractorMOG(history=self.bgSub_history_states, nmixtures=self.bgSub_MOG_nGaussians, 
                                                                                    backgroundRatio=self.bgSub_MOG_bgRatio, noiseSigma=10)
        elif self.bgSub_combo.get () == "MoG2":
            self.background_substractor = cv2.createBackgroundSubtractorMOG2(history=self.bgSub_history_states, detectShadows = False, varThreshold=300)

    def detection_threshold_adjust (self, value):
        self.detection_threshold = round (value, 3)
        self.detection_threshold_value.configure (text=f"{self.detection_threshold:.3f}")

    def toggle_detection (self):
        pass
        # if self.detection_enabled.get ():
        #     self.detection_threshold_slider.configure (state = 'normal')
        # else:
        #     self.detection_threshold_slider.configure (state = 'disabled')

    def bgr_to_hex(self, rgb):
        rgb_str = '%02x%02x%02x' % rgb
        return "#" + rgb_str[4:] + rgb_str[2:4] + rgb_str[:2]
    
    def hex_to_bgr(self, hex_color):
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
            
        bgr = tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0))
        return bgr
    
    def color_picker(self):
        pick_color = AskColor()
        color = pick_color.get()
        self.detection_frame_color_button.configure(border_color = color)
        self.RECT_COLOR = self.hex_to_bgr(color)
    
    def open_camera (self): 
        ret, frame = self.input_vcap.read() 
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC")
        display_frame = None
        if ret:
            frame = cv2.resize(frame, self.FRAME_SIZE) 

            if self.bgSub_toggle.get ():
                fgMask = self.background_substractor.apply(frame)
                photo_image = ctk.CTkImage (dark_image=Image.fromarray(fgMask), size=(250, 250))
                self.bgSub_view.configure(image=photo_image) 
            
            # Check if we should detect people or stream raw video frames
            if self.detection_enabled.get ():
                persons_found = detect (frame, self.model, self.detection_threshold, self.RECT_COLOR)
                if persons_found: 
                    if self.current_rec_frame_count == 0:
                        self.out_cap, self.out_path = setup_output_stream(self.FRAME_SIZE, timestamp, self.storage_path_label.cget("text"))
                    self.out_cap.write(frame) 
                    self.current_rec_frame_count += 1

                elif self.out_cap is not None and self.out_cap.isOpened ():
                    insert_record(self.out_path, self.current_rec_frame_count, timestamp)
                    self.current_rec_frame_count = 0
                    self.out_cap.release()
            elif self.out_cap is not None and self.out_cap.isOpened ():
                insert_record(self.out_path, self.current_rec_frame_count, timestamp)
                self.current_rec_frame_count = 0
                self.out_cap.release()

            # if self.recording_behavior.get () == 'Continuous recording': # 'Recording off', 'Continuous recording', 'Only on detection'
                    
            opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 

            photo_image = ctk.CTkImage (dark_image=Image.fromarray(opencv_image) , size=self.FRAME_SIZE)
            # self.cam_view.photo_image = photo_image 
            self.cam_view.configure(image=photo_image) 

        elif display_frame == None or ret == False:
            self.cam_view.configure (text = 'Empty frame')
            self.cam_view.configure(image=None) 
    
        self.cam_view.after(30, self.open_camera) 


    def cleanup (self):
        self.input_vcap.release ()

