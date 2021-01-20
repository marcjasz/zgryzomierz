import cv2
import numpy as np

from skimage.segmentation import clear_border
from skimage.measure import label, regionprops
from skimage.morphology import square, opening
from geometry import Rectangle, Point

def roi_similarity(frame, a, b):
    def roi_to_hist(roi):
        fragment = roi.clip_to_fit(frame.shape).sample_from_image(frame)
        converted = cv2.cvtColor(fragment, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist(converted, [0], None, [100], [0, 255])
        return cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

    hists = map(roi_to_hist, (a, b))

    return cv2.compareHist(*hists, cv2.HISTCMP_CORREL)

def rois_overlap(rect_a, rect_b):
    (l_a, r_a), (l_b, r_b) = rect_a.corners, rect_b.corners
    x_dist = (min(r_a.x, r_b.x) - max(l_a.x, l_b.x))
    y_dist = (min(r_a.y, r_b.y) - max(l_a.y, l_b.y))

    intersection_area = 0
    if x_dist > 0 and y_dist > 0:
        intersection_area = x_dist * y_dist

    return intersection_area / min(rect_a.area, rect_b.area)

def lines_y(img):
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    equalized = cv2.equalizeHist(gray)
    edges = cv2.Sobel(equalized,cv2.CV_8U,1,0,ksize=3)
    ret,thresh1 = cv2.threshold(edges,70,255,cv2.THRESH_BINARY)
    minLineLength = 30
    maxLineGap = 10
    lines = cv2.HoughLinesP(
        thresh1,
        rho=1,
        theta=1*np.pi/180,
        threshold=30,
        minLineLength=minLineLength,
        maxLineGap=maxLineGap)
    if lines is None:
        return []
    return lines[:, 0]

def adjust_gamma(image, gamma=1.0):
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
        for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def lines_x(img):
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    gray = adjust_gamma(gray, 1.4)
    equalized = cv2.equalizeHist(gray)
    edges = cv2.Sobel(equalized,cv2.CV_8U,0,1,ksize=3)
    ret,thresh1 = cv2.threshold(edges,70,255,cv2.THRESH_BINARY)
    minLineLength = 10
    maxLineGap = 5
    lines = cv2.HoughLinesP(
        thresh1,
        rho=1,
        theta=1*np.pi/180,
        threshold=30,
        minLineLength=minLineLength,
        maxLineGap=maxLineGap)
    if lines is None:
        return []
    return lines

def bgr_to_equalized_hsv(img):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return img_hsv

def remove_large_border_segments(mask_in):
    mask = opening(mask_in, square(3))
    label_image = label(mask)
    for region in regionprops(label_image):
        if region.area > 80 and region.area < 30000:
            minr, minc, maxr, maxc = region.bbox
            maxc -= 1
            maxr -= 1
            mask[minr, minc:maxc] = 0
            mask[maxr, minc:maxc] = 0
            mask[minr:maxr, minc] = 0
            mask[minr:maxr, maxc] = 0

    return clear_border(mask)

def select_regions(mask):
    label_image = label(mask)
    final_mask = np.zeros_like(mask)

    for region in regionprops(label_image):
        if (region.area > 5000
            and region.area < 30000
            and region.solidity > 0.6
            and region.extent > 0.5):
            minr, minc, maxr, maxc = region.bbox
            final_mask[minr:maxr, minc:maxc] = 1

    return final_mask

def split_on_lines(regions, frame):
    rois = []
    for region in regions:
        roi = Rectangle.from_bbox(region.bbox)
        fragment = Rectangle.from_bbox(region.bbox).sample_from_image(frame)
        lines = lines_y(fragment)
        if not len(lines):
            rois.append(roi)
            continue

        distances = []
        line_midpoints = list(map(lambda line: Point((line[0] + line[2]) // 2, (line[1] + line[3]) // 2), lines))
        center = Point(roi.w // 2, roi.h // 2)
        dist_from_center = lambda point: Point.point_distance(center, point)
        distances = list(map(dist_from_center, line_midpoints))

        _, central_line_midpoint = min(zip(distances, line_midpoints), key= lambda pair: pair[0])
        mid_x = central_line_midpoint.x
        left_w = mid_x
        right_w = roi.w - mid_x
        if (left_w / right_w > 0.5 and left_w / right_w < 2):
            left = Rectangle(roi.x, roi.y, left_w, roi.h)
            right = Rectangle(roi.x + left_w, roi.y, right_w, roi.h)
            rois.extend([left, right])
        else:
            rois.append(roi)
    return rois

def detect(frame):
    img_hsv = bgr_to_equalized_hsv(frame)
    mask = cv2.inRange(img_hsv, (10, 0, 0), (80, 360, 360))

    cleared = remove_large_border_segments(mask)
    regions = select_regions(cleared)

    center = Point(cleared.shape[0] // 2, cleared.shape[1] // 2)
    dist_from_center = lambda region: Point.point_distance(center, Point(*region.centroid))

    sorted_regions = sorted(regionprops(label(regions)), key=dist_from_center)
    vertical = filter(lambda region:  abs(region.orientation - sorted_regions[0].orientation) < 1.5, sorted_regions)
    close_to_center = filter(lambda region: dist_from_center(region) < frame.shape[1]/3.2, vertical)

    split = split_on_lines(close_to_center, frame)

    if len(split) < 2:
        return split

    upper, lower = split[:2]
    if upper.x > lower.x:
        lower, upper = upper, lower

    return [upper, lower]