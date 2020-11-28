import numpy as np
import cv2

class MeanshiftTracker:
    def __init__(self):
        self._tracked_regions = []
        self._window_name = 'tracker'
        cv2.namedWindow(self._window_name)

    def add_mark(self, mark, frame):
        roi = MeanshiftTracker.mark_to_region(mark, frame)
        cv2.imshow(self._window_name, roi)
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            hsv_roi,
            np.array([0., 50., 2.]),
            np.array([180., 205., 255.]))
        hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0,180])
        cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
        self._tracked_regions.append({
            'coords': MeanshiftTracker.pos_absolute_to_offset(mark),
            'histogram': hist
        })


    def track(self, frame):
        term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
        marks = []
        for region in self._tracked_regions:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            dst = cv2.calcBackProject([hsv], [0], region['histogram'], [0,180], 1)

            _ret, coords = cv2.meanShift(dst, region['coords'], term_crit)
            region['coords'] = coords
            (x, y, w, h) = coords
            cv2.imshow(self._window_name, frame[y:y+h+5, x:x+w+5])
            marks.append([(x, y), (x+w, y+h)])

        return marks

    @staticmethod
    def mark_to_region(mark, frame, pad=5):
        min_x, max_x = sorted([mark[0][0], mark[1][0]])
        min_y, max_y = sorted([mark[0][1], mark[1][1]])
        x1 = max(0, min_x-pad)
        y1 = max(0, min_y-pad)
        x2 = min(frame.shape[1], max_x+pad)
        y2 = min(frame.shape[0], max_y+pad)
        return frame[y1:y2, x1:x2]

    @staticmethod
    def pos_absolute_to_offset(mark):
        min_x, max_x = sorted([mark[0][0], mark[1][0]])
        min_y, max_y = sorted([mark[0][1], mark[1][1]])

        return (min_x, max_x-min_x, min_y, max_y-min_y)
    