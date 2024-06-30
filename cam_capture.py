import cv2
import os


def get_vcap (channel):
    IP = "10.1.67.111"
    RTSP_PORT = "554"
    CHANNEL = "2"
    USER = "admin"
    PASS = "C@meraUSTO"
    RTSP_LINK = "rtsp://"+USER+":"+PASS+"@"+IP+":"+RTSP_PORT+"/cam/realmonitor?channel="+str (channel)+"&subtype=0"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

    return cv2.VideoCapture(RTSP_LINK, cv2.CAP_FFMPEG)