import cv2
from cam_functions import setup_output_stream, show_frame, get_vcap
from db_manager import insert_record
from yolo_api import detect, load_model

def app ():
    vcap = get_vcap(channel=3)
    model = load_model()
    out_cap, vid_path = setup_output_stream(vcap)
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
            if found:   
                out_cap.write(out_frame)
                duration = out_cap.get(cv2.CAP_PROP_POS_MSEC)
                people_num = 0
                insert_record(vid_path, people_num , duration)
    vcap.release()
    out_cap.release()

if __name__ == '__main__':
    app ()
    

