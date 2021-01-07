import cv2
import numpy as np

from skimage.segmentation import clear_border
from skimage.measure import label, regionprops
from skimage.morphology import closing, square, erosion
from geometry import Rectangle

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
            rois.append(Rectangle.from_bbox(region.bbox))

    if len(rois) == 1:
        rois = [*rois[0].vertical_split()]

    return rois
