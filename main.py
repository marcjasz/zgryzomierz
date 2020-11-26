import cv2
from managers import WindowManager, CaptureManager

class App:
    def __init__(self):
        self._window_manager = WindowManager(
            'App', self.on_keypress
        )
        self._capture_manager = CaptureManager(
            cv2.VideoCapture('data/P1.mp4'), self._window_manager, scale = 0.25
        )
        self._track_marks = []

    def run(self):
        self._window_manager.create_window()
        frame_generator = self.frames()
        frame = next(frame_generator)
        self._capture_manager.paused = True
        while self._window_manager.window_created and frame is not None:
            frame = next(frame_generator)

            self._track_marks = self._window_manager.get_refs()
            self._capture_manager.add_lines(self._track_marks)
            self._window_manager.process_events()
            #zaznaczanie

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
        elif keycode == 27: #escape
            print("exiting")
            self._window_manager.destroy_window()
        elif keycode == 0x0D: #enter
            if not self._capture_manager.paused:
                print("stop film")
                self._capture_manager.paused = True
            else:
                print("start film")
                self._capture_manager.paused = False


if __name__ == "__main__":
    App().run()
