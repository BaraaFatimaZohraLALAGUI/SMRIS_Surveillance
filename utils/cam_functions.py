import cv2
import os

# Get input capture info 
def get_vcap_info(vcap):
    vcap_width     = int(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))   # float `width`
    vcap_height    = int(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # float `height`
    vcap_fps       = int(vcap.get(cv2.CAP_PROP_FPS))
    return vcap_width, vcap_height, vcap_fps


def setup_output_stream(frame_size, timestamp, recording_path):
    w, h = frame_size
    try:  
        if not os.path.exists(recording_path):
            os.makedirs() 
    except OSError:  
        print('Could not create directory') 

    output_vid_path = os.path.join(recording_path, f'rec_{timestamp}.mp4')
    out_cap = cv2.VideoWriter(output_vid_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (w, h))

    return out_cap, output_vid_path

def get_vcap (channel):
    IP = "10.1.67.111"
    RTSP_PORT = "554"
    USER = "admin"
    PASS = "C@meraUSTO"
    RTSP_LINK = "rtsp://"+USER+":"+PASS+"@"+IP+":"+RTSP_PORT+"/cam/realmonitor?channel="+str (channel)+"&subtype=0"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

    return cv2.VideoCapture(RTSP_LINK, cv2.CAP_FFMPEG)

