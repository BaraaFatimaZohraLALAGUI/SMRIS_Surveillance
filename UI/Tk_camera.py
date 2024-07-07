import customtkinter as ctk
import cv2 
from PIL import Image 
from ultralytics import YOLO
from cam_capture import get_vcap

### initial setup

# Load YOLO model 
model = YOLO ('models\\yolov10n.pt') 

FRAME_SCALE = .3
FRAME_WIDTH, FRAME_HEIGHT = (640, 480) 
FRAME_SIZE = (FRAME_WIDTH, FRAME_HEIGHT)
RECT_COLOR = (255, 255, 0)
  
app = ctk.CTk () 
app.title ("SMRIS AI Surveillance")
# app.state('zoomed')
app._state_before_windows_set_titlebar_color = 'zoomed'
  
# Bind the app with Escape keyboard to quit app whenever pressed 
app.bind('<Escape>', lambda e: app.quit()) 


### CAMERA FRAME
camera_frame = ctk.CTkFrame (app) # text="Camera Feed", font= ('Calibri 14 bold')
camera_frame.pack (side='left', expand=True, fill='y', pady=20, ipady=20)

# Channel combobox 
channel_var = ctk.StringVar (value="1")
channel_combo = ctk.CTkComboBox (camera_frame, values=['1', '2', '3', '4'], variable=channel_var, command = lambda event: combo_select (int (channel_var.get ())))

channel_label = ctk.CTkLabel (camera_frame, text='Channel ' + channel_var.get (), font=('Calibri', 24, 'bold')) 
channel_label.pack (side='top')

# Create a label and display it on app 
cam_label = ctk.CTkLabel (camera_frame, text='') 
cam_label.pack(expand=False, fill='x', pady=10, padx=10, side='top') 
channel_combo.pack (side='top')

# Detection toggle button 
toggle_var = ctk.BooleanVar (value=False)
detection_toggle = ctk.CTkSwitch(camera_frame, text='Enable people detection', variable=toggle_var) # style='info.Roundtoggle.Toolbutton'
detection_toggle.pack (side='top', pady=10)
  

vcap = get_vcap (channel = int (channel_var.get ()))

def combo_select (channel): 
    global vcap
    channel_label.configure (text = f"Channel {channel}")
    vcap = get_vcap (channel = channel)


def open_camera(): 

    ret, frame = vcap.read() 
    display_frame = None
    if ret:
        frame = cv2.resize(frame, FRAME_SIZE) # fx = FRAME_SCALE, fy = FRAME_SCALE
        # Check if we should detect people or stream raw video frames
        if toggle_var.get ():
            result = model (frame, save=False, verbose=False) ## Inference 
            persons_found = False
            if len (result[0]):
                for i in range (len (result[0].boxes.xyxy)): # Iterate over the objects in a single image
                    cls_idx = result[0].boxes.cls[i]
                    cls_name = model.names[int (cls_idx)]
                    if cls_name != 'person' or result[0].boxes.conf[i] < .65: continue
                    persons_found = True
                    x1, y1, x2, y2 = map(int, result[0].boxes.xyxy[i].tolist())
                    out_img = cv2.rectangle(frame, (x1, y1), (x2, y2), RECT_COLOR, 2)
    
            if persons_found:
                display_frame = out_img
            else:
                display_frame = frame

        else:
            display_frame = frame

        # Convert image from one color space to other 
        opencv_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGBA) 
    
        # Capture the latest frame and transform to image 
        pil_image = Image.fromarray(opencv_image) 

        photo_image = ctk.CTkImage (dark_image=pil_image, size=FRAME_SIZE)
    
        # Displaying photoimage in the label 
        cam_label.photo_image = photo_image 
    
        # Configure image in the label 
        cam_label.configure(image=photo_image) 
    elif display_frame == None or ret == False:
        cam_label['text'] = 'Empty frame'
  
    cam_label.after(5, open_camera) 

open_camera ()
app.mainloop() 