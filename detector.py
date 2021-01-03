import cv2
import numpy as np

from skimage.segmentation import clear_border
from skimage.measure import label, regionprops
from skimage.morphology import closing, square, erosion

def detect(frame, inverse_mask=False):
    img = frame
    img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
    img_bgr = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(img_hsv, (7, 0, 0), (170, 360, 360))
    if inverse_mask:
        mask = np.logical_not(mask)

    mask = erosion(mask, square(3))
    mask = erosion(mask, square(3))
    closed = closing(mask, square(1))
    cleared = clear_border(closed)
    label_image = label(cleared)

    rois = []
    for region in regionprops(label_image):
        if region.area > 1600:
            min_y, min_x, max_y, max_x = region.bbox
            rois.append((min_x, min_y, max_x-min_x, max_y-min_y))

    if len(rois) == 1:
        roi = rois[0]
        rois = [
            (roi[0], roi[1], roi[2]//2, roi[3]),
            (roi[0] + roi[2]//2, roi[1], roi[2]//2, roi[3])
        ]

    return rois
