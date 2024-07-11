import cv2 
from ultralytics import YOLO


def detect(frame, model, detection_threshold, rect_color):
    # Get class names 
    class_names = model.names
    people_found = False
    # frame_resized = cv2.resize (frame, (0, 0), fx=.5, fy=.5)
    result = model (frame, save=False, verbose=False) ## Inference 

    if len (result[0]): # If no objects have been detected 
        for i in range (len (result[0].boxes.xyxy)): # Iterate over the objects in a single image
            cls_idx = result[0].boxes.cls[i]
            cls_name = class_names[int (cls_idx)]
            if cls_name != 'person' or result[0].boxes.conf[i] < detection_threshold : continue
            people_found = True

            x1, y1, x2, y2 = map(int, result[0].boxes.xyxy[i].tolist())
            cv2.rectangle(frame, (x1, y1), (x2, y2), rect_color, 2)
            
    return people_found
    
models = {'Nano' : 'models\\yolov10n.pt', 'Small' : 'models\\yolov10s.pt', 'Medium' : 'models\\yolov10m.pt'}
def load_model (model_name='Nano'):
    return YOLO (models[model_name])