import cv2
from managers import WindowManager, CaptureManager

class App:
    def __init__(self):
        self._window_manager = WindowManager(
            'App', self.on_keypress, self.draw_line
        )
        self._capture_manager = CaptureManager(
            cv2.VideoCapture('data/P1.mp4'), self._window_manager, scale = 0.5
            #cv2.VideoCapture(0), self._window_manager, scale = 0.5
        )

    def run(self):
        self._window_manager.create_window()
        while self._window_manager.window_created:
            if self._capture_manager.video_start:
                self._capture_manager.enter_frame()
                frame = self._capture_manager.frame
                self._capture_manager.exit_frame()
            self._window_manager.process_events()
            #zaznaczanie

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
            if not self._capture_manager.is_starting_video:
                print("stop film")
                self._capture_manager.stop_video()
            else:
                print("start film")
                self._capture_manager.start_video()

    def draw_line(self, ref):
        cv2.line(self._capture_manager.frame, ref[0], ref[1], (255, 0, 0), 5)
        self._capture_manager.preview_window_manager.show(self._capture_manager.frame)
if __name__ == "__main__":
    App().run()
