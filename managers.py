import cv2
import numpy
import time

class CaptureManager:
    def __init__(self,
                 capture,
                 preview_window_manager = None,
                 scale = 1.0):
        self.preview_window_manager = preview_window_manager
        self.paused = False
        self._capture = capture
        self._entered_frame = False
        self._frame = None
        self._image_filename = None
        self._video_filename = None
        self._video_encoding = None
        self._video_writer = None
        self._video_start = None
        self._start_time = None
        self._frames_elapsed = 0
        self._fps_estimate = None
        self._rois_to_draw = []
        self._lines_to_draw = []
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
            self._entered_frame = self.paused or self._capture.grab()

    def add_rois(self, rois):
        self._rois_to_draw = rois

    def add_lines(self, lines):
        self._lines_to_draw = lines

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
            self.show_frame()

        if self.is_writing_image:
            cv2.imwrite(self._image_filename, self._frame)
            self._image_filename = None

        self._write_video_frame()

        if not self.paused:
            self._frame = None
        self._entered_frame = False

    def draw_rois(self):
        for roi in self._rois_to_draw:
            p1, p2 = roi.corners
            p1 = tuple(map(int, p1.coords))
            p2 = tuple(map(int, p2.coords))
            cv2.rectangle(self._frame, p1, p2, (255, 0, 0), 2)

    def draw_lines(self):
        for p1, p2 in self._lines_to_draw:
            p1 = tuple(map(int, p1.coords))
            p2 = tuple(map(int, p2.coords))
            cv2.line(self._frame, p1, p2, (255, 255, 0), 1)

    def show_frame(self):
        self.draw_rois()
        self.draw_lines()
        self.preview_window_manager.show(self._frame)

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
    def __init__(self, window_name, keypress_callback=None):
        self.keypress_callback = keypress_callback
        self._refs = []
        self._current_ref = []
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
            self._current_ref = [(x, y)]
        elif event == cv2.EVENT_LBUTTONUP:
            self._current_ref.append((x, y))
            self._refs.append(self._current_ref)
            print(self._current_ref)

    def get_refs(self):
        new_refs, self._refs = self._refs, []
        return new_refs
