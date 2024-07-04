from cam_capture import get_vcap
import customtkinter as ctk 
from ultralytics import YOLO
from PIL import Image 
import cv2 

class App (ctk.CTk):
    def __init__ (self, app_name="SMRIS AI Surveillance"):
        super ().__init__ ()
        self.title (app_name)
        self._state_before_windows_set_titlebar_color = 'zoomed'
        self.bind('<Escape>', lambda e: self.quit()) 

        self.channels = ['1', '2', '3', '4']
        self.selected_channel = ctk.StringVar (value=self.channels[0])
        self.detection_enabled = ctk.BooleanVar (value=False)
        self.input_vcap = get_vcap (channel = int (self.selected_channel.get ()))

        self.model = YOLO ('models\\yolov10s.pt') 

        self.detection_threshold = .65

        self.FRAME_SCALE = .3
        self.FRAME_WIDTH, self.FRAME_HEIGHT = (640, 480) 
        self.FRAME_SIZE = (self.FRAME_WIDTH, self.FRAME_HEIGHT)
        self.RECT_COLOR = (255, 255, 0)

    def run (self):
        self.ui_setup ()
        self.open_camera ()
        self.mainloop ()
        self.cleanup ()

    def ui_setup (self):
        self.camera_frame = ctk.CTkFrame (self) 
        self.camera_frame.pack (side='left', expand=True, fill='y', pady=20, ipady=20)

        self.channel_label = ctk.CTkLabel (self.camera_frame, text='Channel ' + self.selected_channel.get (), font=('Calibri', 24, 'bold')) 
        self.channel_label.pack (side='top')

        self.cam_view = ctk.CTkLabel (self.camera_frame, text='') 
        self.cam_view.pack(expand=False, fill='x', pady=10, padx=10, side='top') 

        self.channel_combo = ctk.CTkComboBox (self.camera_frame, values=self.channels, variable=self.selected_channel, command = lambda event: self.channel_select ())
        self.channel_combo.pack (side='top')


        ### Detection control 
        self.detection_frame = ctk.CTkFrame (self.camera_frame, bg_color='transparent')
        self.detection_frame.pack (side='top', pady=10, padx=40, expand=False, fill='x')

        self.detection_frame.columnconfigure (0, weight=1)
        self.detection_frame.columnconfigure (1, weight=1)
        self.detection_frame.columnconfigure (2, weight=1)
        self.detection_frame.rowconfigure (0, weight=1)
        self.detection_frame.rowconfigure (1, weight=1)

        self.detection_toggle = ctk.CTkSwitch(self.detection_frame, text='Enable people detection', variable=self.detection_enabled, command=self.toggle_detection, font=("Calibri", 16)) 
        self.detection_toggle.grid (row=0, column = 0, pady=10, columnspan=3)

        self.detection_threhold_label = ctk.CTkLabel (self.detection_frame, text="Set detection threhold", font=("Calibri", 16))
        self.detection_threhold_label.grid (row=1, column = 0, padx=5, pady=7, sticky='e')

        self.detection_threshold_slider = ctk.CTkSlider(master=self.detection_frame, from_=0.2, to=.95, command= self.detection_threhold_adjust) 
        self.detection_threshold_slider.grid (row=1, column = 1, padx=5, pady=7, sticky='ew')

        self.detection_threhold_value = ctk.CTkLabel (self.detection_frame, text=f"{self.detection_threshold:.3f}", font=("Calibri", 16))
        self.detection_threhold_value.grid (row=1, column = 2, padx=5, pady=7, sticky='w')

    def channel_select (self):
        self.channel_label.configure (text = f"Channel {self.selected_channel.get ()}")
        self.vcap = get_vcap (channel = self.selected_channel.get ())

    def detection_threhold_adjust (self, value):
        self.detection_threshold = round (value, 3)
        self.detection_threhold_value.configure (text=f"{self.detection_threshold:.3f}")

    def toggle_detection (self):
        pass
        # if self.detection_enabled.get ():
        #     self.detection_threshold_slider.configure (state = 'normal')
        # else:
        #     self.detection_threshold_slider.configure (state = 'disabled')

    def open_camera (self): 

        ret, frame = self.input_vcap.read() 
        display_frame = None
        if ret:
            frame = cv2.resize(frame, self.FRAME_SIZE) 

            # Check if we should detect people or stream raw video frames
            if self.detection_enabled.get ():
                result = self.model (frame, save=False, verbose=False) ## Inference 

                if len (result[0]):
                    for i in range (len (result[0].boxes.xyxy)): # Iterate over the objects in a single image
                        cls_idx = result[0].boxes.cls[i]
                        cls_name = self.model.names[int (cls_idx)]
                        if cls_name != 'person' or result[0].boxes.conf[i] < self.detection_threshold: continue
                        x1, y1, x2, y2 = map(int, result[0].boxes.xyxy[i].tolist())
                        frame = cv2.rectangle(frame, (x1, y1), (x2, y2), self.RECT_COLOR, 1)

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