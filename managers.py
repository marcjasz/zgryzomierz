import cv2
import numpy
import time

from sympy import false, true


class CaptureManager:
    def __init__(self,
                 capture,
                 preview_window_manager = None,
                 scale = 1.0):
        self.preview_window_manager = preview_window_manager
        self._capture = capture
        self._entered_frame = False
        self._frame = None
        self._image_filename = None
        self._video_filename = None
        self._video_encoding = None
        self._video_writer = None
        self._video_start = None
        self.video_start = true
        self._start_time = None
        self._frames_elapsed = 0
        self._fps_estimate = None
        self._size = (int(scale * self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                      int(scale * self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    @property
    def frame(self):
        if self._entered_frame and self._frame is None:
            _, self._frame = self._capture.retrieve()
            self._frame = cv2.resize(self._frame, self._size, interpolation = cv2.INTER_AREA)
        return self._frame

    @property
    def is_writing_image(self):
        return self._image_filename is not None

    @property
    def is_writing_video(self):
        return self._video_filename is not None

    @property
    def is_starting_video(self):
        return self._video_start is not None

    def enter_frame(self):
        assert not self._entered_frame, 'previous frame was not exited'

        if self._capture is not None:
            self._entered_frame = self._capture.grab()
    
    def exit_frame(self):
        if self.frame is None:
            self._entered_frame = False
            return
        
        if self._frames_elapsed == 0:
            self._start_time = time.time()
        else:
            time_elapsed = time.time() - self._start_time
            self._fps_estimate = self._frames_elapsed / time_elapsed
        self._frames_elapsed += 1

        if self.preview_window_manager is not None:
            mirrored_frame = numpy.fliplr(self._frame).copy()
            self.preview_window_manager.show(mirrored_frame)
        
        if self.is_writing_image:
            cv2.imwrite(self._image_filename, self._frame)
            self._image_filename = None

        self._write_video_frame()
    
        self._frame = None
        self._entered_frame = False

    def write_image(self, filename):
        self._image_filename = filename

    def start_writing_video(
        self, filename,
        encoding = cv2.VideoWriter_fourcc('I', '4', '2', '0')):
        self._video_filename = filename
        self._video_encoding = encoding

    def stop_writing_video(self):
        self._video_filename = None
        self._video_encoding = None
        self._video_writer = None

    def stop_video(self):
        self.video_start = false
        self._video_start = ''

    def start_video(self):
        self.video_start = true
        self._video_start = None

    def _write_video_frame(self):
        if not self.is_writing_video:
            return

        if self._video_writer is None:
            fps = self._capture.get(cv2.CAP_PROP_FPS)
            if fps == 0.0:
                if self._frames_elapsed < 20:
                    return
                else:
                    fps = self._fps_estimate
            self._video_writer = cv2.VideoWriter(self._video_filename, self._video_encoding, fps, self._size)

        self._video_writer.write(self._frame)


class WindowManager:
    def __init__(self, window_name, keypress_callback=None, draw=None, ref=[]):
        self.keypress_callback = keypress_callback
        self.draw = draw
        self._ref = ref
        self._window_name = window_name
        self._window_created = False

    @property
    def window_created(self):
        return self._window_created

    def create_window(self):
        cv2.namedWindow(self._window_name)
        cv2.setMouseCallback(self._window_name, self.click)
        self._window_created = True

    def show(self, frame):
        cv2.imshow(self._window_name, frame)
    
    def destroy_window(self):
        cv2.destroyWindow(self._window_name)
        self._window_created = False

    def process_events(self):
        keycode = cv2.waitKey(1)
        if self.keypress_callback is not None and keycode != -1:
            keycode &= 0xFF
            self.keypress_callback(keycode)

    def click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self._ref = [(x, y)]
        elif event == cv2.EVENT_LBUTTONUP:
            self._ref.append((x, y))
            self.draw(self._ref)



