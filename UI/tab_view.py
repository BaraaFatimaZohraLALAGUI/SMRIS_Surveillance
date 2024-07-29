import datetime
import os
import customtkinter as ctk 
from tkinter import ttk
from PIL import Image 
import cv2
from UI.SpinBox import IntSpinbox
from db.db_manager import delete_record, get_records_all, insert_record
from utils.cam_functions import get_vcap, setup_output_stream
from utils.utils import bgr_to_hex, hex_to_bgr
from utils.yolo_api import detect, load_model 
from utils.constants import *
from CTkColorPicker import *
from CTkTable import *
from tkcalendar import Calendar


class TabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.channels = ['1', '2', '3', '4']
        self.models = ['YOLOv9 Tiny', 'YOLOv10 Nano', 'YOLOv10 Small', 'YOLOv10 Medium', 'YOLOv10 Big', 'YOLOv10 Large', 'YOLOv10 Extra Large']

        self.selected_channel = ctk.StringVar (value=self.channels[3])
        self.data = []

        self.selected_model = ctk.StringVar (value=self.models[0])
        self.detection_enabled = ctk.BooleanVar (value=False)

        self.model = load_model('YOLOv9 Tiny')

        self.detection_threshold = .25
        self.current_rec_frame_count = 0

        self.rect_color = (255, 255, 0)

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
        self.bgSub_MOG2_detectShadows = ctk.BooleanVar(value= False)
        self.MoG2_threshold = 25


        ### LIVE VIEW TAB

        self.live_view_tab = self.add('Live Feed')

        self.live_frame = ctk.CTkFrame (self.live_view_tab, fg_color='transparent')
        self.live_frame.pack (expand=True, fill='both', pady=20, padx = 60)
        
        self.camera_frame = ctk.CTkFrame (self.live_frame, corner_radius=10) 
        self.camera_frame.pack (side='left', expand=False, fill='y', pady=10, padx=20)

        self.cam_ip_frame = ctk.CTkFrame (self.camera_frame)
        self.cam_ip_frame.pack (expand=False, fill='x', pady=20, padx=40)

        self.ip_entry_field = ctk.CTkEntry (self.cam_ip_frame, textvariable=self.camera_ip_address, corner_radius = 0, font=STANDARD_FONT, border_color= VIOLET_DARK)
        self.ip_entry_field.pack (side='left', expand=True, fill='x')

        self.channel_label = ctk.CTkLabel (self.camera_frame, text='Channel ' + self.selected_channel.get (), font=('Calibri', 24, 'bold')) 
        self.channel_label.pack (side='top')

        self.cam_connect_button = ctk.CTkButton (self.cam_ip_frame, text="Connect", command = self.channel_select, fg_color= VIOLET_DARK, hover_color= VIOLET_LIGHT ,corner_radius = 0, font=STANDARD_FONT, width=200)
        self.cam_connect_button.pack (side='right', expand=False, fill='both')

        self.cam_view = ctk.CTkLabel (self.camera_frame, text='', corner_radius=15) 
        self.cam_view.pack(expand=False, fill='x', pady=15, padx=40, side='top') 

        # self.channel_combo = ctk.CTkComboBox (self.camera_frame, values=self.channels, variable=self.selected_channel, command = lambda event: self.channel_select ())
        # self.channel_combo.pack (side='top')

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

        self.channel_top_left = ctk.CTkButton (master=self.channel_selection_frame, image=top_left_icon, text="", command=lambda : self.channel_select (4), font=STANDARD_FONT, fg_color='transparent', bg_color='transparent', border_color=VIOLET_DARK, hover_color = VIOLET_LIGHT ,border_width=2, corner_radius=10)
        self.channel_top_left.grid (row=0, column=0, sticky='news', padx=5, pady=5)

        self.channel_top_right = ctk.CTkButton (self.channel_selection_frame, image=top_right_icon, text="", command=lambda : self.channel_select (1), font=STANDARD_FONT, fg_color='transparent', bg_color='transparent', border_color=VIOLET_DARK, hover_color = VIOLET_LIGHT ,border_width=2, corner_radius=10)
        self.channel_top_right.grid (row=0, column=1, sticky='news', padx=5, pady=5)

        self.channel_bottom_left = ctk.CTkButton (self.channel_selection_frame, image=bottom_left_icon, text="", command=lambda : self.channel_select (3), font=STANDARD_FONT, fg_color='transparent', bg_color='transparent', border_color=VIOLET_DARK, hover_color = VIOLET_LIGHT, border_width=2, corner_radius=10)
        self.channel_bottom_left.grid (row=1, column=0, sticky='news', padx=5, pady=5)

        self.channel_bottom_right = ctk.CTkButton (self.channel_selection_frame, image=bottom_right_icon, text="", command=lambda : self.channel_select (2), font=STANDARD_FONT,  fg_color='transparent', bg_color='transparent', border_color=VIOLET_DARK, hover_color = VIOLET_LIGHT, border_width=2, corner_radius=10)
        self.channel_bottom_right.grid (row=1, column=1, sticky='news', padx=5, pady=5)

        ### Detection control 
        self.detection_frame = ctk.CTkFrame (self.live_frame, bg_color='transparent', corner_radius=10)
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

        self.detection_toggle = ctk.CTkSwitch(self.detection_frame, text='Enable detection', variable=self.detection_enabled, switch_width=50, command=self.toggle_detection, font=STANDARD_FONT, fg_color= VIOLET_DARK, progress_color= VIOLET_LIGHT) 
        self.detection_toggle.grid (row=0, column = 0, pady= 20, padx = 50, columnspan=1, sticky='w')

        self.detection_frame_color_button = ctk.CTkButton(self.detection_frame, text="Detection frame color", command=self.color_picker, font=STANDARD_FONT, width=130, height=40, corner_radius=20, border_color=bgr_to_hex(self.rect_color),  border_width=1, fg_color= 'transparent')
        self.detection_frame_color_button.grid(row=0, column=1, pady=20, padx=30, columnspan=2, sticky='ew')
             
        # Background substraction
        self.bgSub_frame = ctk.CTkFrame (self.detection_frame, fg_color='transparent', border_color="#454545", border_width=1)
        self.bgSub_frame.grid (row=1, column=0, columnspan=3, sticky='news', padx=30, pady=10)
        self.bgSub_frame.columnconfigure (0, weight=1)
        self.bgSub_frame.columnconfigure (1, weight=1)
        self.bgSub_frame.rowconfigure (0, weight=1)
        self.bgSub_frame.rowconfigure (1, weight=1)
        self.bgSub_frame.rowconfigure (2, weight=1)

        self.bgSub_toggle_var = ctk.BooleanVar (value=True)
        self.bgSub_toggle = ctk.CTkSwitch(self.bgSub_frame, text='Enable background substraction', switch_width=50, command=self.toggle_bgSub, font=STANDARD_FONT, fg_color= VIOLET_DARK, progress_color= VIOLET_LIGHT, variable=self.bgSub_toggle_var) 
        self.bgSub_toggle.grid (row=0, column = 0, pady= 10, padx = 10, columnspan=2, sticky='w')

        self.bgSub_label = ctk.CTkLabel (self.bgSub_frame, text= 'Select a background substraction method', font=STANDARD_FONT)
        self.bgSub_label.grid (row=1, column=0, pady=10, padx=10, sticky='w')

        self.bgSub_combo = ctk.CTkComboBox (self.bgSub_frame, values=self.bg_substraction_methods, font=STANDARD_FONT, width=450, command=self.select_bgSubstractor, dropdown_font=STANDARD_FONT)
        self.bgSub_combo.grid (row=1, column=1, padx=20, pady=10, sticky='e')

        self.bgSub_view = ctk.CTkLabel (self.bgSub_frame, text='', corner_radius=15) 
        self.bgSub_view.grid (row=2, column = 1, pady= 10, padx = 5, sticky='news')

        # BG MOG PARAMETERS 
        self.MOG_params_frame = ctk.CTkFrame (self.bgSub_frame)
        self.MOG_params_frame.grid (row=2, column = 0, pady= 10, padx = 5, sticky='news')

        self.MOG_params_frame.columnconfigure (0, weight=1)
        self.MOG_params_frame.columnconfigure (1, weight=1)
        self.MOG_params_frame.rowconfigure ((0, 1, 2), weight=1)

        history_label = ctk.CTkLabel (self.MOG_params_frame, text= "Number of history entries", font=STANDARD_FONT)
        history_label.grid (row=0, column=0, padx=20, pady=5, sticky='w')
        self.MOG_history_spinbox = IntSpinbox(self.MOG_params_frame, width=150, step_size=1, value=self.bgSub_history_states, button_color=VIOLET_DARK, button_hover_color=VIOLET_LIGHT, command=self.MOG_history_spinbox_callback)
        self.MOG_history_spinbox.grid(row=0, column=1, padx=20, pady=5, sticky='ew')

        nGaussian_mixtures = ctk.CTkLabel (self.MOG_params_frame, text= "Number of Gaussian mixtures", font=STANDARD_FONT)
        nGaussian_mixtures.grid (row=1, column=0, padx=20, pady=5, sticky='w')
        self.nGaussian_mixtures_spinbox = IntSpinbox(self.MOG_params_frame, width=150, step_size=1, value=self.bgSub_MOG_nGaussians, button_color=VIOLET_DARK, button_hover_color=VIOLET_LIGHT, command=self.nGaussians_spinbox_callback)
        self.nGaussian_mixtures_spinbox.grid(row=1, column=1, padx=20, pady=5, sticky='ew')

        bgSub_bgRatio_label = ctk.CTkLabel (self.MOG_params_frame, text= "Background ratio", font=STANDARD_FONT)
        bgSub_bgRatio_label.grid (row=2, column=0, padx=20, pady=5, sticky='w')

        self.bgSub_bgRatio_slider = ctk.CTkSlider(master=self.MOG_params_frame, from_=0, to=1, command= self.bgRatio_slider_callback, width = 150, button_color = '#FFFFFF', button_hover_color='#FFFFFF', progress_color= VIOLET_LIGHT) 
        self.bgSub_bgRatio_slider.set (self.bgSub_MOG_bgRatio)
        self.bgSub_bgRatio_slider.grid (row=2, column = 1, padx=5, pady=5, sticky = 'ew')

        # MOG2 PARAMETER FRAME 
        self.MOG2_params_frame = ctk.CTkFrame (self.bgSub_frame)
        self.MOG2_params_frame.grid (row=2, column = 0, pady= 10, padx = 5, sticky='news')
        self.MOG2_params_frame.grid_remove ()

        self.MOG2_params_frame.columnconfigure ((0, 1), weight=1)
        self.MOG2_params_frame.rowconfigure ((0, 1, 2), weight=1)

        MOG2_history_label = ctk.CTkLabel (self.MOG2_params_frame, text= "Number of history entries", font=STANDARD_FONT)
        MOG2_history_label.grid (row=0, column=0, padx=20, pady=5, sticky='w')
        self.MOG2_history_spinbox = IntSpinbox(self.MOG2_params_frame, width=150, step_size=1, value=self.bgSub_history_states, button_color=VIOLET_DARK, button_hover_color=VIOLET_LIGHT, command=self.MOG_history_spinbox_callback)
        self.MOG2_history_spinbox.grid(row=0, column=1, padx=20, pady=5, sticky='ew')

        mog2_th_label = ctk.CTkLabel (self.MOG2_params_frame, text= "MoG2 Threshold", font=STANDARD_FONT)
        mog2_th_label.grid (row=1, column=0, padx=20, pady=5, sticky='w')

        self.MOG2_threshold_spinbox = IntSpinbox(self.MOG2_params_frame, width=150, step_size=1, value=self.MoG2_threshold, button_color=VIOLET_DARK, button_hover_color=VIOLET_LIGHT, command=self.MOG2_threshold_spinbox_callback)
        self.MOG2_threshold_spinbox.grid(row=1, column=1, padx=20, pady=5, sticky='ew')

        self.bgSub_MOG2_detectShadows_checkbox = ctk.CTkCheckBox(master=self.MOG2_params_frame, text="Detect shadows", variable=self.bgSub_MOG2_detectShadows,command=lambda: self.select_bgSubstractor(None), onvalue=True, offvalue=False, font=STANDARD_FONT, fg_color=VIOLET_LIGHT, hover_color=VIOLET_DARK)
        self.bgSub_MOG2_detectShadows_checkbox.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky='ew')
          

        ## Model selection 
        self.model_select_frame = ctk.CTkFrame (self.detection_frame, fg_color='transparent', border_color="#454545", border_width=1)
        self.model_select_frame.grid (row=2, column=0, columnspan=3, sticky='we', padx=30, pady=20)

        self.model_select_frame.columnconfigure (0, weight=1)
        self.model_select_frame.columnconfigure (1, weight=1)
        self.model_select_frame.rowconfigure (0, weight=1)

        self.model_select_label = ctk.CTkLabel (self.model_select_frame, text="Select an inference model", font=STANDARD_FONT)
        self.model_select_label.grid (row=0, column=0, pady=10, padx=10, sticky='ew')

        self.model_combo = ctk.CTkComboBox (self.model_select_frame, values=self.models, variable=self.selected_model, command = lambda event: self.model_select ())
        self.model_combo.grid (row=0, column=1, padx=40, pady=10, sticky='ew')

        ## Threshold adjusments
        self.threshold_frame = ctk.CTkFrame(self.detection_frame, bg_color = 'transparent', corner_radius = 20, border_color = "#3B3B3B", border_width= 1)
        self.threshold_frame.grid(row=3, column=0, columnspan=3, pady=5, padx=30, ipady=10, sticky='ew')
        self.threshold_frame.columnconfigure (0, weight=1)
        self.threshold_frame.rowconfigure (0, weight=1)
        self.threshold_frame.rowconfigure (1, weight=1)

        self.detection_threshold_slider = ctk.CTkSlider(master=self.threshold_frame, from_=0., to=1., command= self.detection_threshold_adjust, width = 400, button_color = '#FFFFFF', button_hover_color='#FFFFFF', progress_color= VIOLET_LIGHT) 
        self.detection_threshold_slider.set (self.detection_threshold)
        self.detection_threshold_slider.grid (row=0, column = 0, padx=20, pady=0, sticky = 'ew')

        self.detection_threshold_value = ctk.CTkLabel (self.threshold_frame, text=f"{self.detection_threshold:.3f}", font=STANDARD_FONT)
        self.detection_threshold_value.grid (row=0, column = 2, padx=20, pady=0, sticky='w')

        self.detection_threshold_label = ctk.CTkLabel (self.threshold_frame, text="Detection Threshold", font=STANDARD_FONT)
        self.detection_threshold_label.grid (row=2, column = 0, padx=10, pady=0)

        ## Recording behavior
        self.recording_segmented_buttons = ctk.CTkSegmentedButton (self.detection_frame, selected_color=VIOLET_LIGHT, border_width=1, font=STANDARD_FONT, values=['Recording off', 'Continuous recording', 'Only on detection'], unselected_color="#333333", height=40, selected_hover_color=VIOLET_LIGHT, variable=self.recording_behavior)
        self.recording_segmented_buttons.grid (row=4, column = 0, padx=30, pady=20, columnspan=3, sticky='nsew')

        ## Storage folder chooser
        self.folder_chooser_frame = ctk.CTkFrame(self.detection_frame, bg_color = 'transparent', corner_radius = 20, border_color = "#3B3B3B", border_width= 1, height=150)
        self.folder_chooser_frame.grid (row=5, column = 0, padx=30, pady=20, columnspan=3, sticky='nsew')

        self.folder_chooser_button = ctk.CTkButton (self.folder_chooser_frame, text='Choose a storage directory', command=self.select_folder, font=STANDARD_FONT, width=130, height=40, corner_radius=20, border_color=VIOLET_DARK, hover_color=VIOLET_LIGHT,border_width=1, fg_color= VIOLET_DARK)
        self.folder_chooser_button.pack (side='left', pady=20, padx= 20)

        self.storage_path_label = ctk.CTkLabel (self.folder_chooser_frame, text=self.recording_storage_path, font=STANDARD_FONT)
        self.storage_path_label.pack (side='left')


        ### PLAYBACK VIEW
        self.playback_view_tab = self.add('Playback')
        self.playback_frame = ctk.CTkFrame (self.playback_view_tab, fg_color='transparent')
        self.playback_frame.pack (expand=True, fill='both', pady=20, padx = 60)

        self.video_frame = ctk.CTkFrame(self.playback_frame, fg_color='transparent')
        self.video_frame.pack(side = 'left')
        
        self.video_label = ctk.CTkLabel(self.video_frame, text = 'No video selected', font= ('Calibri', 20))
        self.video_label.pack(side = 'top')    

        self.vid_display = ctk.CTkLabel (self.video_frame, text='', corner_radius=15) 
        self.vid_display.pack(expand=False, fill='x', pady=15, padx=40, side='top') 


        self.navigation_frame = ctk.CTkFrame(self.playback_frame, fg_color='transparent')
        self.navigation_frame.pack(side = 'right')

        self.search_frame = ctk.CTkFrame(self.navigation_frame, fg_color='transparent')
        self.search_frame.pack(side = 'top', ipady = 20)

        self.dates = ctk.CTkFrame(self.search_frame, fg_color = 'transparent')
        self.dates.pack()
        self.dates.columnconfigure (0, weight=1)
        self.dates.columnconfigure (1, weight=1)
        self.dates.rowconfigure (0, weight=1)
        self.dates.rowconfigure (1, weight=1)
  
        self.calendar_window = None
        self.start_date_label = ctk.CTkLabel(self.dates, text='Start Date', font = STANDARD_FONT)
        self.start_date_label.grid(column = 0, row = 0, pady = 5, padx = 20)
        self.start_date_entry = ctk.CTkEntry(self.dates, width=160, height = 32, font = STANDARD_FONT, placeholder_text= f'{datetime.datetime.now(tz=datetime.timezone.utc).strftime("%d-%m-%Y")}', placeholder_text_color='white', text_color='white', fg_color=VIOLET_DARK, border_color= VIOLET_LIGHT, border_width= 1, corner_radius= 8)
        self.start_date_entry.grid(column = 0, row = 1, pady = 5, padx = 20)

        self.start_date_entry.bind("<Button>", self.pop_calendar)

        self.end_date_label = ctk.CTkLabel(self.dates, text='End Date', font = STANDARD_FONT)
        self.end_date_label.grid(column = 1, row = 0, pady = 5, padx = 20)
        self.end_date_entry = ctk.CTkEntry(self.dates, width=160, height = 32, font = STANDARD_FONT, placeholder_text= f'{datetime.datetime.now(tz=datetime.timezone.utc).strftime("%d-%m-%Y")}', placeholder_text_color='white', text_color='white', fg_color=VIOLET_DARK, border_color= VIOLET_LIGHT, border_width= 1, corner_radius= 8)
        self.end_date_entry.grid(column = 1, row = 1, pady = 5, padx = 20)

        self.end_date_entry.bind("<Button>", self.pop_calendar)

        self.table_manage_frame = ctk.CTkFrame(self.navigation_frame, fg_color='transparent')
        self.table_manage_frame.pack(side = 'bottom', expand=True, fill='both')

        self.table_labels = ctk.CTkSegmentedButton(self.table_manage_frame, dynamic_resizing=True, values = ['Path', 'Number of Frames', 'Timestamp'], width = 600, height = 30, fg_color= VIOLET_DARK,bg_color=VIOLET_DARK, unselected_color= VIOLET_DARK, unselected_hover_color= VIOLET_DARK, selected_hover_color= VIOLET_DARK,selected_color= VIOLET_DARK)
        self.table_labels.pack(side= 'top', expand = True, fill = 'x', pady = 0)
        self.data_table_frame = ctk.CTkScrollableFrame(self.table_manage_frame, width = 900, height = 350, fg_color='transparent')
        self.data_table_frame.pack(side = 'top', expand=True, fill='x', pady = 0)
        data_cursor = get_records_all()


        for entry in data_cursor:
            row = [entry['Path'], entry['Number of Frames'], entry['Timestamp'] ]
            self.data.append(row)

        self.data_table = CTkTable(self.data_table_frame, column = 3, values = self.data, bg_color = 'transparent', font=STANDARD_FONT, corner_radius = 10, command= self.select_row)
        self.data_table.pack(expand = True, fill = 'both', padx = 0, pady = 0)

        self.prev_table_row = -1

        self.data_table.edit_row(len(self.data)-1, corner_radius=0)
        self.data_table.edit_row(0, corner_radius=0)

        self.play_vid_button = ctk.CTkButton(self.table_manage_frame, width = 120, height= 30, corner_radius= 8, fg_color = GREEN_DARK, hover_color= GREEN_LIGHT, text = 'Play video', command = self.play_video_playback)
        self.play_vid_button.pack(side = 'left', padx=10, pady=10)
        
        self.delete_button = ctk.CTkButton(self.table_manage_frame, width = 120, height= 30, corner_radius= 8, fg_color = VIOLET_DARK, hover_color= 'red', text = 'Delete row', command= self.delete_row)
        self.delete_button.pack(side = 'left', padx=10, pady=10)


    def pop_calendar(self, event):

        if self.calendar_window and self.calendar_window.winfo_exists():
            self.calendar_window.lift()
            return
        
        x, y = self.start_date_entry.winfo_rootx(), self.start_date_entry.winfo_rooty()
        self.calendar_window = ctk.CTk()
        self.calendar_window.geometry(f"360x300+{x}+{y}")

        frame = ctk.CTkFrame(self.calendar_window)
        frame.pack(fill="both", padx=10, pady=10, expand=True)

        style = ttk.Style(self.calendar_window)
        style.theme_use("default")

        cal = Calendar(frame, selectmode='day', locale='en_US', disabledforeground='red', cursor="hand2", background=VIOLET_LIGHT, selectbackground= VIOLET_DARK)
        cal.pack(side = 'top', fill="both", expand=True, padx=10, pady=10)

        time_frame = ctk.CTkFrame(frame)
        time_frame.pack(side = 'bottom', fill="both", padx=10, pady=10, expand=True)

        time_frame.columnconfigure ((0, 1, 2), weight=1)
        time_frame.rowconfigure ((0, 1), weight=1)

        hour_label = ctk.CTkLabel(time_frame, text='hour', font = ('Calibri', 14))
        hour_label.grid(column = 0, row = 0, pady = 0, padx = 20)
        hour_entry = IntSpinbox(time_frame, width=100, height= 30, text_font= ('Calibri', 13), font = ('Calibri', 11), value= 0, step_size=1, button_color= VIOLET_DARK, button_hover_color= VIOLET_LIGHT, min_val= 0, max_val=23)
        hour_entry.grid(column = 0, row = 1)

        min_label = ctk.CTkLabel(time_frame, text='min', font = ('Calibri', 14))
        min_label.grid(column = 1, row = 0, pady = 0, padx = 20)
        minute_entry = IntSpinbox(time_frame, width=100, height= 30, text_font= ('Calibri', 13), value= 0, font = ('Calibri', 11), step_size=1, button_color= VIOLET_DARK, button_hover_color= VIOLET_LIGHT, min_val= 0, max_val=59)
        minute_entry.grid(column = 1 , row = 1)

        sec_label = ctk.CTkLabel(time_frame, text='sec', font = ('Calibri', 14))
        sec_label.grid(column = 2, row = 0, pady = 0, padx = 20)
        sec_entry = IntSpinbox(time_frame, width=100, height= 30, value= 0, text_font= ('Calibri', 13) , font = ('Calibri', 11), step_size=1, button_color= VIOLET_DARK, button_hover_color= VIOLET_LIGHT, min_val= 0, max_val=59)
        sec_entry.grid(column = 2, row = 1)

        self.calendar_window.protocol("WM_DELETE_WINDOW", self.on_calendar_window_close)
        self.calendar_window.mainloop()

    def on_calendar_window_close(self):
        self.calendar_window.destroy()
        self.calendar_window = None

    def play_video_playback(self):
        index = self.prev_table_row
        if index == -1: return
        rec = self.data[index]

        vid_name = rec[0].split ('\\')[-1]
        self.video_label.configure (text=vid_name)
        self.playback_vcap = cv2.VideoCapture(rec[0])
        self.open_playback()

    def open_playback(self):
        ret, frame = self.playback_vcap.read ()

        if ret:
            opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
            photo_image = ctk.CTkImage (dark_image=Image.fromarray(opencv_image) , size=(640, 480))
            self.vid_display.configure(image=photo_image)

            self.vid_display.after (20, self.open_playback)

    def delete_row(self):
        index = self.prev_table_row
        if index != -1:
            self.data_table.delete_row(index)
            rec = self.data[index]
            record = { "Path": rec[0],
                "Number of Frames": rec[1],
                "Timestamp": rec[2],
            }
            delete_record(record)
            try:  
                if os.path.exists(rec[0]):
                    os.remove(rec[0])
            except OSError:  
                print('file not found')  

    def select_row(self, event):
        index = event['row']
        if index == -1 or index == self.prev_table_row:
            return
        if self.prev_table_row != -1:
            self.data_table.edit_row(self.prev_table_row, fg_color='transparent')
        self.data_table.edit_row(index, fg_color = VIOLET_LIGHT)

        self.prev_table_row = index
        return self.data[index][0]

    def select_folder(self):
        folder_path = ctk.filedialog.askdirectory()
        if folder_path == "": return
        self.storage_path_label.configure (text=folder_path.replace ('/', '\\'))


    def toggle_bgSub (self):
        if not self.bgSub_toggle.get ():
            self.self.bgSub_frame.grid_remove ()
        else:
            self.self.bgSub_frame.grid ()

    def bgRatio_slider_callback (self, event):
        self.bgSub_MOG_bgRatio = self.bgSub_bgRatio_slider.get ()
        self.select_bgSubstractor (None)

    def MOG_history_spinbox_callback (self):
        self.bgSub_history_states = int (self.MOG_history_spinbox.get ())
        self.select_bgSubstractor (None)

    def nGaussians_spinbox_callback (self):
        self.bgSub_MOG_nGaussians = int (self.nGaussian_mixtures_spinbox.get ())
        self.select_bgSubstractor (None)

    def MOG2_threshold_spinbox_callback (self):
        self.MoG2_threshold = self.MOG2_threshold_spinbox.get ()
        self.select_bgSubstractor (None)


    def channel_select(self, channel=1):
        self.selected_channel.set(channel)
        self.channel_label.configure(text=f"Channel {channel}")
        self.input_vcap = get_vcap(self.camera_ip_address.get(), channel=channel)
        
        channel_map = {
            4: self.channel_top_left,
            1: self.channel_top_right,
            3: self.channel_bottom_left,
            2: self.channel_bottom_right
        }
        
        for ch, widget in channel_map.items():
            widget.configure(fg_color=VIOLET_LIGHT if ch == channel else "transparent")


    def model_select (self):
        self.model = load_model(self.selected_model.get ())

    def select_bgSubstractor (self, event):
        self.MOG_params_frame.grid ()
        self.MOG2_params_frame.grid_remove ()
        if self.bgSub_combo.get () == "Mixture-of-Gaussian - MoG":
             self.background_substractor = cv2.bgsegm.createBackgroundSubtractorMOG(history=self.bgSub_history_states, nmixtures=self.bgSub_MOG_nGaussians, 
                                                                                    backgroundRatio=self.bgSub_MOG_bgRatio, noiseSigma=10)
        elif self.bgSub_combo.get () == "MoG2":
            self.MOG_params_frame.grid_remove ()
            self.MOG2_params_frame.grid ()
            self.background_substractor = cv2.createBackgroundSubtractorMOG2(history=self.bgSub_history_states, detectShadows = self.bgSub_MOG2_detectShadows.get (), varThreshold=self.MoG2_threshold)


    def detection_threshold_adjust (self, value):
        self.detection_threshold = round (value, 3)
        self.detection_threshold_value.configure (text=f"{self.detection_threshold:.3f}")

    def toggle_detection (self):
        pass
        # if self.detection_enabled.get ():
        #     self.detection_threshold_slider.configure (state = 'normal')
        # else:
        #     self.detection_threshold_slider.configure (state = 'disabled')


    
    def color_picker(self):
        pick_color = AskColor()
        color = pick_color.get()
        self.detection_frame_color_button.configure(border_color = color)
        self.rect_color = hex_to_bgr(color)

        
    def open_camera (self): 
        ret, frame = self.input_vcap.read() 
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%d-%m-%Y_%H-%M-%S_UTC")
        display_frame = None
        if ret:
            frame = cv2.resize(frame, FRAME_SIZE) 

            if self.bgSub_toggle.get ():
                fgMask = self.background_substractor.apply(frame)
                photo_image = ctk.CTkImage (dark_image=Image.fromarray(fgMask), size=(100, 100))
                self.bgSub_view.configure(image=photo_image) 
            
            # Check if we should detect people or stream raw video frames
            if self.detection_enabled.get ():
                persons_found = detect (frame, self.model, self.detection_threshold, self.rect_color)
                if persons_found: 
                    if self.current_rec_frame_count == 0:
                        self.out_cap, self.out_path = setup_output_stream(FRAME_SIZE, timestamp, self.storage_path_label.cget("text"))
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

            photo_image = ctk.CTkImage (dark_image=Image.fromarray(opencv_image) , size=FRAME_SIZE)
            # self.cam_view.photo_image = photo_image 
            self.cam_view.configure(image=photo_image) 

        elif display_frame == None or ret == False:
            self.cam_view.configure (text = 'Empty frame')
            self.cam_view.configure(image=None) 
    
        self.cam_view.after(30, self.open_camera) 
