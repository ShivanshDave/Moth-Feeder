# #---- reference codes ----#
# Camera : def(s) : http://picamera.readthedocs.io/en/release-1.13/_modules/picamera/camera.html
# Motion : basic code - 15.9 : http://picamera.readthedocs.io/en/release-1.13/api_array.html
# CircIO : http://picamera.readthedocs.io/en/release-1.13/api_streams.html

from __future__ import print_function, division
import numpy as np
import picamera
import picamera.array
# import logging as log
import time
import io

# #---- Video parameters ----#
frame_width, frame_height = 640, 480
frame_rotate = 0  # 0 to disable rotation
frame_fps = 30  # to be tested and adjusted
# todo : add 2 different fps for pre-motion and post-motion
duration_premotion = 3
duration_inactivity = 5
frame_timestamp_embbed = 1  # 0 to disable
# todo : add or save timestamps
# todo : add RoI

motion_threshold = 60
motion_min_vectors = 10

# Save video here...
datapath = '/media/pi/lab6'

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
    self.sharpness = 0
    self.contrast = 0
    self.brightness = 50
    self.saturation = 0
    self.iso = 0  # auto
    self.video_stabilization = True
    self.exposure_compensation = 0
    self.exposure_mode = 'auto'
    self.meter_mode = 'average'
    self.awb_mode = 'auto'
    self.image_effect = 'none'
    self.color_effects = None
    self.rotation = frame_rotate
    self.hflip = self.vflip = False
    self.zoom = (0.0, 0.0, 1.0, 1.0)
    self.resolution = (frame_width, frame_height)
    self.framerate = frame_fps


class SysVar():
    motion_detection_flag = False
    last_motion_time = time.time()


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
            SysVar.motion_detection_flag = True
            SysVar.last_motion_time = time.time()
        else:
            if SysVar.motion_detection_flag:
                if (time.time() - SysVar.last_motion_time > duration_inactivity):
                    SysVar.motion_detection_flag = False
                    print('DetectMotion->TimeOut')

print('Check 0.1')ls
with picamera.PiCamera() as camera:
    # decreasing frame_size for detection can speedup process
    with DetectMotion(camera, size=frame_size) as output:
        # initiate circular buffer as stream
        with picamera.PiCameraCircularIO(camera, seconds=duration_premotion) \
                as stream:
            print('Check 0.2')
            _init_defaults(camera)
            print('Check 0.3')
            # uninterrupted recording at port-1
            camera.start_recording(stream, format='h264', splitter_port=1)
            # motion vector analysis at port-2
            print('Check 0.4')
            camera.start_recording('/dev/null', splitter_port=2,
                                   resize=frame_size,
                                   format='h264',
                                   motion_output=output)
            print('Check 0.5')
            camera.wait_recording(2)
            print('Check 0.6')
            # ----------------------------------------------------------------#
            SysVar.motion_detection_flag = False
            try:
                print('--Starting motion triggered video capture--')
                while 1:
                    if SysVar.motion_detection_flag:
                        video_name = datapath + "/" + time.strftime(
                            "pi_vid_%Y%m%d-%H%M%S", time.localtime())
                        print('recording started at {}'.format(video_name))
                        camera.split_recording(video_name + '-post_trigger.h264',
                                               splitter_port=1)
                        print('Check 1')
                        save_buffer_as_video(stream, video_name)
                        print('Check 1.1')
                        while SysVar.motion_detection_flag:
                            camera.wait_recording(1, splitter_port=1)
                        # stop saving in file, start filling buffer again
                        print('Check 1.2')
                        camera.split_recording(stream, splitter_port=1)
                        print('VideoSaved')
            finally:
                print('Stopping Camera')
                camera.stop_recording(splitter_port=1)
                camera.stop_recording(splitter_port=2)
