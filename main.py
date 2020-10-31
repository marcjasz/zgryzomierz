import cv2

videoCapture = cv2.VideoCapture('data/P1.mp4')
fps = videoCapture.get(cv2.CAP_PROP_FPS)
size = (
    videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH),
    videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT)
)

print(fps, size)

clicked = False

def onMouse(event, x, y, flags, param):
    global clicked
    if event == cv2.EVENT_LBUTTONUP:
        clicked = True

cv2.namedWindow('AAA')
cv2.setMouseCallback('AAA', onMouse)

success, frame = videoCapture.read()
while success and cv2.waitKey(1) == -1:
    cv2.imshow('AAA', frame)
    if clicked:
        success, frame = videoCapture.read()