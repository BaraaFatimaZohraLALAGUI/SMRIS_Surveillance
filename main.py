import numpy as np 
import cv2 
from ultralytics import YOLO
from cam_capture import get_vcap

vcap = get_vcap (channel = 1)
vcap.set(3,640)
vcap.set(4,480)

# Get input capture info 
vcap_width     = int(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))   # float `width`
vcap_height    = int(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # float `height`
vcap_fps       = int(vcap.get(cv2.CAP_PROP_FPS))
print (vcap_fps, vcap_width, vcap_height)

# out_cap = cv2.VideoWriter('results\output.mp4', cv2.VideoWriter_fourcc(*"MP4V"), 60.0, (vcap_width,  vcap_height), 0)

# Load YOLO model 
model = YOLO ('models\\yolov8n.pt') 
# Get class names 
class_names = model.names

RECT_COLOR = (0, 0, 255)

def show_frame (img, scale_factor=.5):

    # Resize
    width = int(img.shape[1] * scale_factor)
    height = int(img.shape[0] * scale_factor)

    min_dim = width if width < height else height
    new_dim = (min_dim, min_dim)
    img = cv2.resize (img, new_dim)

    # Display
    cv2.imshow ("Detection", img)

    if cv2.waitKey (2) & 0xFF == ord("q"):
        vcap.release ()
        # out_cap.release ()
        cv2.destroyAllWindows()
        return

# Main loop 
while(True):
    ret, frame = vcap.read()
    if ret == False:
        print("Frame is empty")
        break
    else:

        # out_cap.write (frame)

        result = model (frame, save=False, verbose=False) ## Inference 
        nbr_persons = 0 # Number of detected people 

        if len (result[0]) == 0: # If no objects have been detected 
            continue
        else:
            for i in range (len (result[0].boxes.xyxy)): # Iterate over the objects in a single image
                cls_idx = result[0].boxes.cls[i]
                cls_name = class_names[int (cls_idx)]
                if cls_name != 'person': continue
                nbr_persons += 1

                x1, y1, x2, y2 = map(int, result[0].boxes.xyxy[i].tolist())
                out_img = cv2.rectangle(frame, (x1, y1), (x2, y2), RECT_COLOR, 2)

        if nbr_persons == 0:
            show_frame (frame)
        else:
            show_frame (out_img)

            












