import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __str__(self):
        return f'({self.x}, {self.y})'
    
    @property
    def coords(self):
        return (self.x, self.y)
    
    @staticmethod
    def normalize(point_a, point_b):
        return Point(point_a.x - point_b.x, point_a.y - point_b.y)
    
    @staticmethod
    def point_angle(p1, p2):
        point_vector = Point.normalize(p1, p2)
        return math.degrees(math.atan2(point_vector.y, point_vector.x))


class Rectangle:
    # (x,y) is the top-left coordinate of the rectangle and (w,h) its width and height
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    
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

    def vertical_split(self):
        left = Rectangle(self.x, self.y, self.w//2, self.h)
        right = Rectangle(self.x + self.w//2, self.y, self.w//2, self.h)
        return left, right