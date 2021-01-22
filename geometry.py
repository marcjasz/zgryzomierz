import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f'Point({self.x}, {self.y})'

    @property
    def coords(self):
        return (self.x, self.y)

    @staticmethod
    def normalize(point_a, point_b):
        return Point(point_a.x - point_b.x, point_a.y - point_b.y)

    @staticmethod
    def point_angle(p1, p2):
        point_vector = Point.normalize(p1, p2)
        return (math.degrees(math.atan2(point_vector.y, point_vector.x)) + 360) % 360

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y
    @staticmethod
    def point_distance(p1, p2):
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)


class Rectangle:
    # (x,y) is the top-left coordinate of the rectangle and (w,h) its width and height
    def __init__(self, x, y, w, h):
        self.x = math.ceil(x)
        self.y = math.ceil(y)
        self.w = math.ceil(w)
        self.h = math.ceil(h)

    def __str__(self):
        return f'({self.x}, {self.y}, {self.w}, {self.h})'

    @staticmethod
    def from_bbox(bbox):
        min_y, min_x, max_y, max_x = bbox
        return Rectangle(min_x, min_y, max_x-min_x, max_y-min_y)
    
    @property
    def parameters(self):
        return self.x, self.y, self.w, self.h

    @property
    def corners(self):
        return Point(self.x, self.y), Point(self.x + self.w, self.y + self.h)

    @property
    def area(self):
        return self.w * self.h

    @property
    def center(self):
        return Point(self.x + self.w//2, self.y + self.h//2)

    def sample_from_image(self, image):
        return image[self.y : self.y + self.h + 1, self.x : self.x + self.w + 1, :]

    def clip_to_fit(self, shape):
        return Rectangle(
            max(0, self.x),
            max(0, self.y),
            min(shape[0], self.w),
            min(shape[1], self.h)
        )
