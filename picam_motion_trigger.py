# #---- reference codes ----#
# Camera : def(s) : http://picamera.readthedocs.io/en/release-1.13/_modules/picamera/camera.html
# Motion : basic code - 15.9 : http://picamera.readthedocs.io/en/release-1.13/api_array.html
# CircIO : http://picamera.readthedocs.io/en/release-1.13/api_streams.html
# e.g. python picam_motion_trigger.py '/home/pi' 1280 720 10 90 70 15 3 3 1

from __future__ import print_function, division
import numpy as np
import picamera
import picamera.array
# import logging as log
import time
import io
import sys

# #---- Video parameters ----#
try:
    # ARG : < path W-H-FPS-ROT MotTh-MotVec Tpre Tpost debug >
    datapath = sys.argv[1] if len(sys.argv) >= 2 else '/home/pi'
    frame_width = int(sys.argv[2]) if len(sys.argv) >= 3 else 640
    frame_height = int(sys.argv[3]) if len(sys.argv) >= 4 else 480
    frame_fps = int(sys.argv[4]) if len(sys.argv) >= 5 else 30
    frame_rotate = int(sys.argv[5]) if len(sys.argv) >= 6 else 90
    motion_threshold = int(sys.argv[6]) if len(sys.argv) >= 7 else 60
    motion_min_vectors = int(sys.argv[7]) if len(sys.argv) >= 8 else 10
    duration_premotion = int(sys.argv[8]) if len(sys.argv) >= 9 else 3
    duration_inactivity = int(sys.argv[9]) if len(sys.argv) >= 10 else 3
    debug = int(sys.argv[10]) if len(sys.argv) >= 11 else False
except:
    print('--Error in SysArgv--\nTaking Defaults...')
    datapath = '/media/pi/lab6'
    frame_width, frame_height = 640, 480
    frame_rotate = 90  # 0 to disable rotation
    frame_fps = 30  # to be tested and adjusted
    # todo : add 2 different fps for pre-motion and post-motion
    motion_threshold = 60
    motion_min_vectors = 10
    duration_premotion = 3
    duration_inactivity = 3
    debug = False

frame_timestamp_embbed = 0  # 0 to disable
# todo : add or save timestamps
# todo : add RoI

# #----Program Variables----#
frame_size = (frame_width, frame_height)


def save_buffer_as_video(_stream, _video_name):
    with io.open(_video_name + '-pre_trigger.h264', 'wb') as output:
        for frame in _stream.frames:
            if frame.frame_type == picamera.PiVideoFrameType.sps_header:
                _stream.seek(frame.position)
                break
        while True:
            data = _stream.read1()
            if not data:
                break
            output.write(data)
    # reset the stream before the next capture
    _stream.seek(0)
    _stream.truncate()


def _init_defaults(self):
    # self.sharpness = 0
    # self.contrast = 0
    # self.brightness = 50
    # self.saturation = 0
    # self.iso = 0  # auto
    # self.video_stabilization = True
    # self.exposure_compensation = 0
    # self.exposure_mode = 'auto'
    # self.meter_mode = 'average'
    # self.awb_mode = 'auto'
    # self.image_effect = 'none'
    # self.color_effects = None
    if frame_rotate:
        self.rotation = frame_rotate
    # self.hflip = self.vflip = False
    # self.zoom = (0.0, 0.0, 1.0, 1.0)
    self.resolution = (frame_width, frame_height)
    self.framerate = frame_fps


class SysVar:
    motion_detection_flag = False
    last_motion_time = time.time()
    i2 = 0


class DetectMotion(picamera.array.PiMotionAnalysis):
    def analyse(self, a):
        a = np.sqrt(
            np.square(a['x'].astype(np.float)) +
            np.square(a['y'].astype(np.float))
        ).clip(0, 255).astype(np.uint8)
        # todo-RoI will crop/bin image here...
        # If there're more than (motion_min_vectors) vectors with a magnitude
        # greater than (motion_threshold), then say we've detected motion
        if (a > motion_threshold).sum() > motion_min_vectors:
            SysVar.last_motion_time = time.time()
            SysVar.motion_detection_flag = True
            if debug:
                SysVar.i2 += 1
                print('--MOTION DETECTED--{}'.format(SysVar.i2))

        else:
            if SysVar.motion_detection_flag:
                if (time.time() - SysVar.last_motion_time) > duration_inactivity:
                    SysVar.motion_detection_flag = False
                    SysVar.i2 = 0
                    print('--DetectMotion -> TimeOut--')


if debug:
    print('0.1-Videos will be saved at {}'.format(datapath))
with picamera.PiCamera() as camera:
    # decreasing frame_size for detection can speedup process
    with DetectMotion(camera, size=frame_size) as output:
        # initiate circular buffer as stream
        with picamera.PiCameraCircularIO(camera, seconds=duration_premotion) \
                as stream:
            if debug:
                print('0.2-Setting-up camera parameters.\nRes:{},{}\nFPS:{}'
                      .format(frame_width, frame_height, frame_fps))
            _init_defaults(camera)
            # uninterrupted recording at port-1
            camera.start_recording(stream, format='h264', splitter_port=1)
            # motion vector analysis at port-2
            camera.start_recording('/dev/null', splitter_port=2,
                                   resize=frame_size,
                                   format='h264',
                                   motion_output=output)
            if debug:
                print('0.3-Recording started at port1 (Video) and port2 (Motion'
                      'Detect @ Full frame)')
            camera.wait_recording(2)
            # ----------------------------------------------------------------#
            # SysVar.motion_detection_flag = False
            try:
                print('--Starting motion triggered video capture--')
                while 1:
                    if SysVar.motion_detection_flag:
                        video_name = datapath + "/" + time.strftime(
                            "pi_vid_%Y%m%d-%H%M%S", time.localtime())
                        if debug:
                            print('1.0 - recording started at {}'.format
                                  (video_name))
                        camera.split_recording(
                            video_name + '-post_trigger.h264',
                            splitter_port=1)
                        save_buffer_as_video(stream, video_name)
                        if debug:
                            print('1.1 - PreTrigger Video saved.')
                        while SysVar.motion_detection_flag:
                            camera.wait_recording(1, splitter_port=1)
                        # stop saving in file, start filling buffer again
                        camera.split_recording(stream, splitter_port=1)
                        if debug:
                            print('1.2 - PostTrigger Video Saved.')
            finally:
                print('\n--Closing Camera--\n')
                camera.stop_recording(splitter_port=1)
                camera.stop_recording(splitter_port=2)
