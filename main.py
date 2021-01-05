import cv2
from managers import WindowManager, CaptureManager
from detector import detect
import math
from math import atan2, degrees

class App:
    def __init__(self, create_tracker_fun):
        #self._recognition_program = gui.main()
        self._window_manager = WindowManager(
            'App', self.on_keypress
        )
        self._capture_manager = CaptureManager(
            # cv2.VideoCapture(0), self._window_manager, scale = 1
            cv2.VideoCapture('data/P1.mp4'), self._window_manager, scale = 0.25
            #cv2.VideoCapture(name), self._window_manager, scale=0.25
        )
        self._track_marks = []
        self._create_tracker_fun = create_tracker_fun
        self._multi_tracker = cv2.MultiTracker_create()
        self._angle = 999
        self._angle_change = []


    def run(self):
        self._window_manager.create_window()
        frame_generator = self.frames()
        frame = next(frame_generator)
        self._capture_manager.paused = False
        for ref in detect(frame):
            self._track_marks.append(ref)
            self._multi_tracker.add(self._create_tracker_fun(), frame, ref)

        while self._window_manager.window_created and frame is not None:
            frame = next(frame_generator)

            if self._angle == 999 and len(self._track_marks) == 2:
                self._angle = math.degrees(math.atan2(self._track_marks[0][1] - self._track_marks[1][1],
                                                      self._track_marks[0][0] - self._track_marks[1][0]))
                print('fhhkjs' + str(self._angle))

            ok, rois = self._multi_tracker.update(frame)
            if ok:
                self._capture_manager.add_rois(rois)
                if self._angle != 999:
                    if len(self._angle_change) != 0:
                        if self.to_angle(rois.tolist()) != self._angle_change[-1]:
                            self._angle_change.append(self.to_angle(rois.tolist()))
                    else:
                        self._angle_change.append(self.to_angle(rois.tolist()))
                    print(self._angle_change[-1])
                    #print(rois)
                    self._capture_manager.add_angle([[rois[0][0], rois[0][1] + 0.5*rois[0][3],
                                                      rois[1][0], rois[0][1] + 0.5*rois[0][3]], #rois[1][1] + 0.5*rois[1][3]],
                                                      [rois[0][0], rois[0][1] + 0.5*rois[0][3],
                                                       rois[1][0], self.count_point(rois)]])
            else:
                print("Tracking failure")

            self._window_manager.process_events()

    def to_angle (self, rois):
        new_angle = math.degrees(math.atan2(rois[0][1] - rois[1][1], rois[0][0] - rois[1][0]))
        result = new_angle - self._angle
        if result < -180:
           result = 360 + result
        return result

    def count_point(self, rois):
        b = math.hypot(rois[1][0] - rois[0][0], (rois[0][1] + 0.5 * rois[0][3]) -(rois[0][1] + 0.5 * rois[0][3]))

        #b = math.dist([rois[0][0], rois[0][1] + 0.5 * rois[0][3]], [rois[1][0], rois[1][1] + 0.5 * rois[1][3]])
        c = b / math.cos(math.radians(self._angle_change[-1]))
        a = c * math.sin(math.radians(self._angle_change[-1]))
        if self._angle_change[-1] > 0:
            #print(str(a) + 'hdkhhkjdkj')
            new_y = rois[0][1] + 0.5*rois[0][3] + a
        else:
            new_y = rois[0][1] + 0.5 * rois[0][3] - a
        return new_y


    def ref_to_roi(self, mark):
        min_x, max_x = sorted([mark[0][0], mark[1][0]])
        min_y, max_y = sorted([mark[0][1], mark[1][1]])

        return (min_x, min_y, max_x-min_x, max_y-min_y)

    def frames(self):
        while True:
            self._capture_manager.enter_frame()

            yield self._capture_manager.frame

            self._capture_manager.exit_frame()

    def on_keypress(self, keycode):
        if keycode == 32: # space
            print("screenshot created")
            self._capture_manager.write_image('out/screenshot.png')
        elif keycode == 9: # tab
            if not self._capture_manager.is_writing_video:
                print("recording started")
                self._capture_manager.start_writing_video('out/screencast.avi')
            else:
                print("recording finished")
                self._capture_manager.stop_writing_video()
        elif keycode == 27: # escape
            print("exiting")
            self._window_manager.destroy_window()
        elif keycode == 0x0D: # enter
            if not self._capture_manager.paused:
                print("stop film")
                self._capture_manager.paused = True
            else:
                print("start film")
                self._capture_manager.paused = False


if __name__ == "__main__":

    App(cv2.TrackerMedianFlow_create).run()
