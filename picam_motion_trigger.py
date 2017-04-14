# #---- reference codes ----#
# Camera : def(s) :
# http://picamera.readthedocs.io/en/release-1.13/_modules/picamera/camera.html
# Motion : basic code - 15.9 :
# http://picamera.readthedocs.io/en/release-1.13/api_array.html
# CircIO : http://picamera.readthedocs.io/en/release-1.13/api_streams.html
# # RES : V2-Mode-4 : 1640x1232 @ 0.1 - 40 FPS
# # RES : V2-Mode-6 : 1280x720 @ 40 - 90 FPS

from __future__ import print_function, division
import numpy as np
import picamera
import picamera.array
import time
import io


class SysVar:
    motion_detection_flag = False
    motion_check_pause = True
    last_motion_time = 0
    mot_cnt = -1000


class DetectMotion(picamera.array.PiMotionAnalysis):
    def analyse(self, a):
        if not SysVar.motion_check_pause:
            a = np.sqrt(
                np.square(a['x'].astype(np.float)) +
                np.square(a['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
            # todo-RoI will crop image here...
            # If there're more than (motion_min_vectors) vectors with a magnitude
            # greater than (motion_threshold), then say we've detected motion
            if (a > motion_threshold).sum() > motion_min_vectors:
                if debug:
                    SysVar.mot_cnt += 1
                    print('--MOTION DETECTED--{}'.format(SysVar.mot_cnt))
                SysVar.last_motion_time = time.time()
                SysVar.motion_detection_flag = True
            else:
                if SysVar.motion_detection_flag:
                    if (time.time() - SysVar.last_motion_time) > \
                            duration_inactivity:
                        SysVar.motion_detection_flag = False
                        if debug:
                            SysVar.mot_cnt = -1000
                        print('--DetectMotion -> TimeOut--')


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


def main():
    with picamera.PiCamera() as camera:
        # initiate circular buffer as stream
        with picamera.PiCameraCircularIO(camera, seconds=duration_premotion) \
                as stream:
            # decreasing frame_size for detection can speedup process
            with DetectMotion(camera, size=frame_size) as output:

                _init_defaults(camera)
                if debug:
                    print('0.1 -> Cam Configured, starting to record...')

                # uninterrupted recording at port-1
                camera.start_recording(stream, format='h264', splitter_port=1)
                # motion vector analysis at port-2
                SysVar.motion_check_pause = True
                camera.start_recording('/dev/null', splitter_port=2,
                                       resize=frame_size,
                                       format='h264',
                                       motion_output=output)
                camera.wait_recording(2)
                if debug:
                    print('0.2 -> Recording started at port1 (Video) and port2 '
                          '(Motion Detect @ Full frame)')

                try:
                    print('--Starting motion triggered video capture--')
                    SysVar.motion_check_pause = False
                    while 1:
                        if SysVar.motion_detection_flag:
                            # get a unique name and start storing video
                            video_name = time.strftime("pi_vid_%Y%m%d-%H%M%S",
                                                       time.localtime())
                            video_name = datapath + video_name
                            camera.split_recording(video_name + '-post_trigger'
                                                                '.h264',
                                                   splitter_port=1)
                            if debug:
                                print('1.0 - recording started as {}'
                                      .format(video_name))
                                SysVar.mot_cnt = 0

                            # wait for time-out
                            while SysVar.motion_detection_flag:
                                camera.wait_recording(1, splitter_port=1)

                            # save preTrigger video with sane unique name
                            save_buffer_as_video(stream, video_name)
                            if debug:
                                print('1.1 - PreTrigger Video saved.')

                            # stop saving in file, start filling buffer again
                            camera.split_recording(stream, splitter_port=1)
                            if debug:
                                print('1.2 - PostTrigger Video Saved.')
                        camera.wait_recording(0.2)    
                finally:
                    print('\n--Closing Camera--\n')
                    camera.stop_recording(splitter_port=1)
                    camera.stop_recording(splitter_port=2)


if __name__ == '__main__':  
    import argparse

    # #---- Video parameters ----#
    parser = argparse.ArgumentParser(description='Get settings for recording.')
    parser.add_argument('-p', '--path', help='data output path </path/folder/>',
                        dest='datapath', default='/home/pi/', type=str)
    parser.add_argument('-wf', '--width', help='frame width.',
                        dest='frame_width', default=1280, type=int)
    parser.add_argument('-hf', '--height', help='frame_height',
                        dest='frame_height', default=720, type=int)
    parser.add_argument('-f', '--fps', help='Recording FPS',
                        dest='frame_fps', default=40, type=int)
    parser.add_argument('-rt', '--rotate', help='Frame rotation - CW',
                        dest='frame_rotate', default=90, type=int)
    parser.add_argument('-pr', '--premot', help='duration_premotion',
                        dest='duration_premotion', default=3, type=int)
    parser.add_argument('-ps', '--postmot', help='duration_inactivity',
                        dest='duration_inactivity', default=3, type=int)
    parser.add_argument('-th', '--threshold', help='motion_threshold',
                        dest='motion_threshold', default=60, type=int)
    parser.add_argument('-nv', '--numvector', help='motion_min_vectors',
                        dest='motion_min_vectors', default=10, type=int)
    parser.add_argument('-d', '--debug', dest='debug', default=False,
                        help='for details, (makes program slow)')
    args = parser.parse_args()

    datapath = args.datapath
    frame_width = args.frame_width
    frame_height = args.frame_height
    frame_fps = args.frame_fps
    frame_rotate = args.frame_rotate
    motion_threshold = args.motion_threshold
    motion_min_vectors = args.motion_min_vectors
    duration_premotion = args.duration_premotion
    duration_inactivity = args.duration_inactivity
    debug = args.debug
    # todo : add or save timestamps
    # todo : add RoI
    frame_size = (frame_width, frame_height)

    if debug:
        print("datapath = {}; frame_width = {}; frame_fps = {}; frame_rotate ="
              " {}; motion_threshold = {}; motion_min_vectors = {}; duration_pr"
              "emotion= {}; duration_inactivity = {}; debug = {};"
              .format(datapath, frame_width, frame_fps, frame_rotate,
                      motion_threshold, motion_min_vectors, duration_premotion,
                      duration_inactivity, debug))

    main()
