import sys
from sense_hat import SenseHat

sense = SenseHat()
sense.set_rotation(0)
sense.clear()
sense.low_light = True

red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)

#  set border
X = [0, 150, 0]  # light green
O = [0, 0, 0]  # off

border = [
O, O, O, O, O, O, O, O,
O, X, X, X, X, X, X, O,
O, X, O, O, O, O, X, O,
O, X, O, O, O, O, X, O,
O, X, O, O, O, O, X, O,
O, X, O, O, O, O, X, O,
O, X, X, X, X, X, X, O,
O, O, O, O, O, O, O, O
]

sense.set_pixels(border)

#  init bubble
x1 = 3
x2 = 4
y1 = 3
y2 = 4

accel_threshold = 0.1

prev_x1 = 0
prev_y1 = 0
prev_x2 = 0
prev_y2 = 0

while True:
    try:
        raw_Gs = sense.get_accelerometer_raw()
        x_Gs = raw_Gs['x']
        y_Gs = raw_Gs['y']
        z_Gs = raw_Gs['z']

        if x_Gs >= (-1 * accel_threshold) and x_Gs <= accel_threshold:
            x1 = 3
            x2 = 4
        if y_Gs >= (-1 * accel_threshold) and y_Gs <= accel_threshold:
            y1 = 3
            y2 = 4
        
        if x_Gs <= (-1 * accel_threshold):
            x1 = 4
            x2 = 5
        if y_Gs <= (-1 * accel_threshold):
            y1 = 4
            y2 = 5
        
        if x_Gs >= accel_threshold:
            x1 = 2
            x2 = 3
        if y_Gs >= accel_threshold:
            y1 = 2
            y2 = 3

        if x1 != prev_x1:
            sense.set_pixel(prev_x1, prev_y1, 0, 0, 0)
            sense.set_pixel(prev_x1, prev_y2, 0, 0, 0)
        if x2 != prev_x2:
            sense.set_pixel(prev_x2, prev_y1, 0, 0, 0)
            sense.set_pixel(prev_x2, prev_y2, 0, 0, 0)
        if y1 != prev_y1:
            sense.set_pixel(prev_x1, prev_y1, 0, 0, 0)
            sense.set_pixel(prev_x2, prev_y1, 0, 0, 0)
        if y2 != prev_y2:
            sense.set_pixel(prev_x1, prev_y2, 0, 0, 0)
            sense.set_pixel(prev_x2, prev_y2, 0, 0, 0)

        sense.set_pixel(x1, y1, 0, 0, 255)
        sense.set_pixel(x1, y2, 0, 0, 255)
        sense.set_pixel(x2, y1, 0, 0, 255)
        sense.set_pixel(x2, y2, 0, 0, 255)

        prev_x1 = x1
        prev_y1 = y1
        prev_x2 = x2
        prev_y2 = y2
            
    except KeyboardInterrupt:
        sense.clear()
