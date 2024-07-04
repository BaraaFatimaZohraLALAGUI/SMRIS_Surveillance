import tkinter as tk
import ttkbootstrap as ttk
import cv2 
from PIL import Image, ImageTk 
# from ultralytics import YOLO
from cam_functions import get_vcap, setup_output_stream
from yolo_api import detect, load_model

### initial setup
# Get the four video captures

FRAME_SCALE = .3
RECT_COLOR = (255, 255, 0)

width, height = 800, 600
  
app = ttk.Window (themename='darkly') 
app.state('zoomed')
  
# Bind the app with Escape keyboard to quit app whenever pressed 
app.bind('<Escape>', lambda e: app.quit()) 


### CAMERA FRAME
camera_frame = tk.LabelFrame (app, text="Camera Feed", font= ('Calibri 14 bold'))
camera_frame.pack (side='left', expand=True, fill='y', pady=20, ipady=20)

# Channel combobox 
channel_var = tk.IntVar (value=1)
channel_combo = ttk.Combobox (camera_frame, values=[1, 2, 3, 4], textvariable=channel_var)

channel_label = ttk.Label (camera_frame, text='Channel ' + str (channel_var.get ()), font='Calibri 18 bold') 
channel_label.pack (side='top')

channel_combo.bind ('<<ComboboxSelected>>', lambda event: combo_select (channel_var.get ()))

# Create a label and display it on app 
cam_label = ttk.Label(camera_frame, width=100) 
cam_label.pack(expand=False, fill='x', pady=10, padx=10, side='top') 
channel_combo.pack (side='top')

# Detection toggle button 
toggle_var = tk.BooleanVar (value=False)
detection_toggle = ttk.Checkbutton(camera_frame, text='Toggle people detection', style='info.Roundtoggle.Toolbutton', variable=toggle_var)
detection_toggle.pack (side='top', pady=10)
  

vcap = get_vcap (channel = channel_var.get ())

def combo_select (channel): 
    global vcap
    channel_label.configure (text = f"Channel {channel}")
    vcap = get_vcap (channel = channel)

def open_camera(): 

    model = load_model()
    out_cap = setup_output_stream(vcap)

    ret, frame = vcap.read() 
    display_frame = None
    if ret:
        frame = cv2.resize(frame, (640, 480)) # fx = FRAME_SCALE, fy = FRAME_SCALE

        # Check if we should detect people or stream raw video frames
        if toggle_var.get ():
            persons_found, out_frame = detect (frame, model)
            if persons_found:   out_cap.write(out_frame)   

        else:
            display_frame = frame

        # Convert image from one color space to other 
        opencv_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGBA) 
    
        # Capture the latest frame and transform to image 
        captured_image = Image.fromarray(opencv_image) 

    
        # Convert captured image to photoimage 
        photo_image = ImageTk.PhotoImage(image=captured_image) 
    
        # Displaying photoimage in the label 
        cam_label.photo_image = photo_image 
    
        # Configure image in the label 
        cam_label.configure(image=photo_image) 
    elif display_frame == None or ret == False:
        cam_label['text'] = 'Empty frame'
  
    cam_label.after(5, open_camera) 

open_camera ()
app.mainloop() 