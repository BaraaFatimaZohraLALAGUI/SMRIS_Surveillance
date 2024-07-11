import datetime
import customtkinter as ctk 
from PIL import Image 
import cv2
from db.db_manager import insert_record
from utils.cam_functions import get_vcap, setup_output_stream
from utils.yolo_api import detect, load_model 

from CTkColorPicker import *

class App (ctk.CTk):
    def __init__ (self, app_name="SMRIS AI Surveillance"):
        super ().__init__ ()
        self.title (app_name)
        self._state_before_windows_set_titlebar_color = 'zoomed'
        self.bind('<Escape>', lambda e: self.quit()) 

        self.channels = ['1', '2', '3', '4']
        self.selected_channel = ctk.StringVar (value=self.channels[3])
        self.detection_enabled = ctk.BooleanVar (value=False)

        self.model = load_model('Nano')

        self.detection_threshold = .25
        self.current_rec_frame_count = 0

        self.FRAME_SCALE = .3
        self.FRAME_WIDTH, self.FRAME_HEIGHT = (800, 600) 
        self.FRAME_SIZE = (self.FRAME_WIDTH, self.FRAME_HEIGHT)
        self.RECT_COLOR = (255, 255, 0)

        self.input_vcap = get_vcap (channel = int (self.selected_channel.get ()))
        self.out_cap = None

    def run (self):
        self.ui_setup ()
        self.open_camera ()
        self.mainloop ()
        self.cleanup ()

    def ui_setup (self):
        self.parent_frame = ctk.CTkFrame (self, bg_color='transparent')
        self.parent_frame.pack (expand=True, fill='both', pady=40, padx = 60)
        
        self.camera_frame = ctk.CTkFrame (self.parent_frame) 
        self.camera_frame.pack (side='left', expand=False, fill='y', pady=20, padx=20)

        self.channel_label = ctk.CTkLabel (self.camera_frame, text='Channel ' + self.selected_channel.get (), font=('Calibri', 24, 'bold')) 
        self.channel_label.pack (side='top')

        self.cam_view = ctk.CTkLabel (self.camera_frame, text='') 
        self.cam_view.pack(expand=False, fill='x', pady=10, padx=10, side='top') 

        self.channel_combo = ctk.CTkComboBox (self.camera_frame, values=self.channels, variable=self.selected_channel, command = lambda event: self.channel_select ())
        self.channel_combo.pack (side='top')


        ### Detection control 
        self.detection_frame = ctk.CTkFrame (self.parent_frame, bg_color='transparent')
        self.detection_frame.pack (side='right', pady=20, padx=20, expand=True, fill='both')

        self.detection_frame.columnconfigure (0, weight=1)
        self.detection_frame.columnconfigure (1, weight=1)
        self.detection_frame.columnconfigure (2, weight=1)
        self.detection_frame.rowconfigure (0, weight=1)
        self.detection_frame.rowconfigure (1, weight=1)


        self.detection_frame_color_button = ctk.CTkButton(self.detection_frame, text="Detection frame color", command=self.color_picker, font=("Calibri", 16), width=130, height=40, corner_radius=20, border_color=self.bgr_to_hex(self.RECT_COLOR),  border_width=1, fg_color= 'transparent')
        self.detection_frame_color_button.grid(row=0, column=0, pady=20, padx=30)
        self.detection_toggle = ctk.CTkSwitch(self.detection_frame, text='Enable detection', variable=self.detection_enabled, command=self.toggle_detection, font=("Calibri", 16), progress_color= '#1D4C86', button_color='#6DA9F5') 
        self.detection_toggle.grid (row=0, column = 1, pady= 20, padx = 30, columnspan=2)

        self.threshold_frame = ctk.CTkFrame(self.detection_frame, bg_color = 'transparent', corner_radius = 20, width = 450, height = 85, border_color = "#3B3B3B", border_width= 1)
        self.threshold_frame.grid(row=1, column=0, columnspan=3, pady=5, padx=5, ipady=20)
        self.threshold_frame.columnconfigure (0, weight=1)
        self.threshold_frame.rowconfigure (0, weight=1)
        self.threshold_frame.rowconfigure (1, weight=1)

        self.detection_threshold_slider = ctk.CTkSlider(master=self.threshold_frame, from_=0.2, to=.95, command= self.detection_threshold_adjust, width = 400, button_color = '#6DA9F5', progress_color= '#1D4C86') 
        self.detection_threshold_slider.set (self.detection_threshold)
        self.detection_threshold_slider.grid (row=0, column = 0, padx=20, pady=5, sticky = 'ew')

        self.detection_threshold_value = ctk.CTkLabel (self.threshold_frame, text=f"{self.detection_threshold:.3f}", font=("Calibri", 16))
        self.detection_threshold_value.grid (row=0, column = 2, padx=10, pady=5, sticky='ew')

        self.detection_threshold_label = ctk.CTkLabel (self.threshold_frame, text="Detection Threshold", font=("Calibri", 16))
        self.detection_threshold_label.grid (row=1, column = 0, padx=5, pady=0)

    def channel_select (self):
        self.channel_label.configure (text = f"Channel {self.selected_channel.get ()}")
        self.input_vcap = get_vcap (channel = self.selected_channel.get ())

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
            
            # Check if we should detect people or stream raw video frames
            if self.detection_enabled.get ():
                persons_found = detect (frame, self.model, self.detection_threshold, self.RECT_COLOR)
                if persons_found: 
                    if self.current_rec_frame_count == 0:
                        self.out_cap, self.out_path = setup_output_stream(self.FRAME_SIZE, timestamp)
                    self.out_cap.write(frame) 
                    self.current_rec_frame_count += 1

                elif self.out_cap is not None and self.out_cap.isOpened ():
                    insert_record(self.out_path, self.current_rec_frame_count, timestamp)
                    self.current_rec_frame_count = 0
                    self.out_cap.release()
                    
            opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA) 
        
            # Capture the latest frame and transform to image 
            pil_image = Image.fromarray(opencv_image) 

            photo_image = ctk.CTkImage (dark_image=pil_image, size=self.FRAME_SIZE)
        
            # Displaying photoimage in the label 
            self.cam_view.photo_image = photo_image 
        
            # Configure image in the label 
            self.cam_view.configure(image=photo_image) 
        elif display_frame == None or ret == False:
            self.cam_view['text'] = 'Empty frame'
    
        self.cam_view.after(5, self.open_camera) 

    def cleanup (self):
        self.input_vcap.release ()


if __name__ == '__main__':
    app = App ()
    app.run ()