import cv2
import os
import datetime

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


# Get input capture info 
def get_vcap_info(vcap):
    vcap_width     = int(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))   # float `width`
    vcap_height    = int(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # float `height`
    vcap_fps       = int(vcap.get(cv2.CAP_PROP_FPS))
    return vcap_width, vcap_height, vcap_fps


def setup_output_stream(frame_size):
    w, h = frame_size
    try:  
        if not os.path.exists('captures_out2'):
            os.makedirs('captures_out2') 
    except OSError as error:  
        print(' -- error creating directory ') 

    timestamp = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC")
    output_vid_path = os.path.join('captures_out2', f'rec_{timestamp}.mp4')
    out_cap = cv2.VideoWriter(output_vid_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (w, h))

    return out_cap, output_vid_path

def get_vcap (channel):
    IP = "10.1.67.111"
    RTSP_PORT = "554"
    CHANNEL = "2"
    USER = "admin"
    PASS = "C@meraUSTO"
    RTSP_LINK = "rtsp://"+USER+":"+PASS+"@"+IP+":"+RTSP_PORT+"/cam/realmonitor?channel="+str (channel)+"&subtype=0"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

    return cv2.VideoCapture(RTSP_LINK, cv2.CAP_FFMPEG)

