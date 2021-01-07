import cv2
import math
from managers import WindowManager, CaptureManager
from detector import detect
from geometry import Point, Rectangle

class VideoAnalysis:
    def __init__(self, create_tracker_fun, file_path):
        self._window_manager = WindowManager(
            'App', self.on_keypress
        )
        self._capture_manager = CaptureManager(
            cv2.VideoCapture(file_path), self._window_manager, scale = 0.25
        )
        self._track_marks = []
        self._create_tracker_fun = create_tracker_fun
        self._multi_tracker = cv2.MultiTracker_create()
        self._base_angle = None
        self._angle_change = []

    def run(self):
        self._window_manager.create_window()
        self._capture_manager.paused = False
        frame_generator = self.frames()
        frame = next(frame_generator)

        for bounding_box in detect(frame)[:2]:
            self._track_marks.append(bounding_box)
            self._multi_tracker.add(self._create_tracker_fun(), frame, bounding_box.parameters)

        previous_angle = None
        if len(self._track_marks) == 2:
            self._base_angle = Point.point_angle(
                self._track_marks[0].corners[0],
                self._track_marks[1].corners[0]
            )

        while self._window_manager.window_created and frame is not None:
            frame = next(frame_generator)

            ok, rois = self._multi_tracker.update(frame)
            if ok:
                upper, lower = Rectangle(*rois[0]), Rectangle(*rois[1])

                current_angle = self.to_angle(upper, lower)
                if current_angle != previous_angle:
                    previous_angle = current_angle
                    self._angle_change.append(self.to_angle(upper, lower))

                base_angle_line = (
                    Point(upper.x, upper.y + upper.h//2),
                    Point(lower.x, upper.y + upper.h//2)
                )
                current_angle_line = (
                    Point(upper.x, upper.y + upper.h//2),
                    self.count_point(current_angle, upper, lower)
                )
                self._capture_manager.add_lines([current_angle_line, base_angle_line])
                self._capture_manager.add_rois([upper, lower])

                if not (previous_angle and self._capture_manager.paused):
                    print(current_angle)
            else:
                print("Tracking failure")

            self._window_manager.process_events()

    def to_angle(self, upper, lower):
        new_angle = Point.point_angle(upper.corners[0], lower.corners[0])
        result = new_angle - self._base_angle
        if result < -180:
            result = 360 + result
        return result

    def count_point(self, angle, upper, lower):
        b = math.hypot(lower.x - upper.x, 0)
        c = b / math.cos(math.radians(angle))
        a = c * math.sin(math.radians(angle))
        new_y = upper.y + 0.5*upper.h + a

        return Point(lower.x, new_y)

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
    file_path = 'data/P1.mp4'
    VideoAnalysis(cv2.TrackerMedianFlow_create, file_path).run()
