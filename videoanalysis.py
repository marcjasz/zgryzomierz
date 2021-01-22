import cv2
import math
from detector import detect, roi_similarity, rois_overlap
from geometry import Point, Rectangle

class VideoAnalysis:
    def __init__(self, capture, finish, queue_angle, queue_distance, queue_distance_max, queue_height):
        self._track_marks = []
        self._create_tracker_fun = cv2.TrackerMedianFlow_create
        self._multi_tracker = cv2.MultiTracker_create()
        self._capture_manager = capture
        self._initial_roi_histograms = []
        self._base_angle = None
        self._queue_angle = queue_angle
        self._queue_distance = queue_distance
        self._queue_distance_max = queue_distance_max
        self._queue_height = queue_height
        self.queue_finish = finish
        self._frame_no = 0

    def run(self):
        self._capture_manager.paused = False
        frame_generator = self.frames()
        frame = next(frame_generator)

        rois = detect(frame)
        self.save_rois(frame, rois)

        previous_angle = None
        while frame is not None:
            frame = next(frame_generator)

            ok, rois = self._multi_tracker.update(frame)
            if ok and len(rois) > 1:
                upper, lower = Rectangle(*rois[0]), Rectangle(*rois[1])

                if not self._frame_no % 100:
                    new_rois = detect(frame)
                    if len(new_rois) >= 2:
                        new_similarity = roi_similarity(frame, *new_rois[:2])
                        old_similarity = roi_similarity(frame, upper, lower)
                        current_overlap = rois_overlap(upper, lower)
                        if old_similarity < 0.4 and new_similarity - old_similarity > 0.4:
                            for pair in zip(new_rois[:2], [upper, lower]):
                                overlap = rois_overlap(*pair)
                                if current_overlap > 0.2 or overlap < 0.4:
                                    self.save_rois(frame, new_rois[:2])

                current_angle = self.to_angle(upper, lower)
                self._queue_angle.put(self.to_angle(upper, lower))
                base_angle_line = (
                    Point(upper.x, upper.y + upper.h//2),
                    Point(lower.x, upper.y + upper.h//2))
                current_angle_line = (
                    Point(upper.x, upper.y + upper.h//2),
                    self.count_point(current_angle, upper, lower))

                self._queue_distance.put(math.hypot(base_angle_line[1].get_x() - current_angle_line[1].get_x(),
                                                    base_angle_line[1].get_y() - current_angle_line[1].get_y()))
                self._queue_distance_max.put(math.hypot(upper.x + upper.w - lower.x, 0))
                self._queue_height.put(upper.w)
                self._capture_manager.add_lines([current_angle_line, base_angle_line])
                self._capture_manager.add_rois([upper, lower])

            else:
                # print("Tracking failure")
                if frame is not None and not self._frame_no % 15:
                    new_rois = detect(frame)
                    self.save_rois(frame, new_rois)

            if frame is None:
                self.queue_finish.put(1)
                break

    def save_rois(self, frame, rois):
        self._multi_tracker = cv2.MultiTracker_create()
        self._track_marks = []
        for bounding_box in rois[:2]:
            self._track_marks.append(bounding_box)
            roi_fragment = bounding_box.clip_to_fit(frame.shape).sample_from_image(frame)
            histogram = cv2.calcHist(roi_fragment, [0], None, [100], [0, 255])
            self._initial_roi_histograms.append(histogram)
            self._multi_tracker.add(self._create_tracker_fun(), frame, bounding_box.parameters)

        if len(self._track_marks) >= 2:
            self._base_angle = Point.point_angle(
                self._track_marks[0].corners[0],
                self._track_marks[1].corners[0]
            )
            self._queue_distance_max.put(0)
            self._queue_distance.put(0)
            self._queue_height.put(0)
            self._queue_angle.put(0)


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

            self._frame_no += 1
            self._capture_manager.exit_frame()
