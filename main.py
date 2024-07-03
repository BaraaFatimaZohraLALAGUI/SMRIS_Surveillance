import numpy as np 
import cv2 
from ultralytics import YOLO
from cam_capture import get_vcap
import os

def detect(frame, model):
    # Get class names 
    class_names = model.names
    people_found = False
    # frame_resized = cv2.resize (frame, (0, 0), fx=.5, fy=.5)
    result = model (frame, save=False, verbose=False) ## Inference 

    if len (result[0]): # If no objects have been detected 
        for i in range (len (result[0].boxes.xyxy)): # Iterate over the objects in a single image
            cls_idx = result[0].boxes.cls[i]
            cls_name = class_names[int (cls_idx)]
            if cls_name != 'person' or result[0].boxes.conf[i] < .65 : continue
            print (result[0].boxes.conf[i])
            people_found = True

            x1, y1, x2, y2 = map(int, result[0].boxes.xyxy[i].tolist())
            out_img = cv2.rectangle(frame, (x1, y1), (x2, y2), RECT_COLOR, 2)
            
    if not people_found:
        return people_found, frame
    else:
        return people_found, out_img

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
        cv2.destroyAllWindows()
        return True
    return False

models = {'Nano' : 'models\\yolov10n.pt', 'Small' : 'models\\yolov10s.pt', 'Medium' : 'models\\yolov10m.pt'}
def load_model (model_name='Small'):
    model = YOLO (models[model_name])
    return model 


RECT_COLOR = (180, 105, 255)




# Get input capture info 
def get_vcap_info(vcap):
    vcap_width     = int(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))   # float `width`
    vcap_height    = int(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # float `height`
    vcap_fps       = int(vcap.get(cv2.CAP_PROP_FPS))
    return vcap_width, vcap_height, vcap_fps


def setup_output_stream(vcap):
    w, h, _ = get_vcap_info(vcap)
    try:  
        if not os.path.exists('captures_out2'):
            os.makedirs('captures_out2') 
    except OSError as error:  
        print(' -- error creating directory ') 

    output_vid_path = os.path.join('captures_out2', 'output.mp4')
    out_cap = cv2.VideoWriter(output_vid_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (w, h))

    return out_cap


def app ():
    vcap = get_vcap(channel=3)
    model = load_model()
    out_cap = setup_output_stream(vcap)
    # Main loop 
    while(True):

        ret, frame = vcap.read()

        if ret == False:
            print("Frame is empty")
            break
            
        else:
            found, out_frame = detect (frame, model)
            quit = show_frame (out_frame, scale_factor=.5)
            if quit: break
            if found:   out_cap.write(out_frame)
    vcap.release()
    out_cap.release()

if __name__ == '__main__':
    app ()
    

