"""

Alignment tool for OpenMV camera.
Displays camera framebuffer (in IDE) with optional, customizable crosshairs.


Customizable parameters:

FRAMESIZE (int):        Framesize configuration (from 'sensor' module)
(CX, CY) (int, int):    Center of cross-hairs (e.g. calibrated optical axis)
COLOR (int):            Crosshairs/line color (0..255: white. 255, black: 0)
SHOW_CROSSHAIRS (bool)  Enable (True) / disable (False) display of crosshairs
SHOW_CENTER (bool)      Enable (True) / disable (False) display of image center
EXPOSURE_US (int)       Camera exposure time [us], None for auto exposure
GAIN_DB (int)           Camera gain [db], None for auto gain


(C) 2025 Felix Althaus

"""



import sensor
import pyb



FRAMESIZE = sensor.VGA      # Sensor framesize (from 'sensor' module)
                            # VGA:   640 x 480 px
                            # WVGA2: 752 x 480 px (for the MT9V034)

(CX, CY) = (320, 240)       # Custom crosshairs center

COLOR = 255                 # Crosshairs color (white: 255, black: 0)

SHOW_CROSSHAIRS = False     # Enable user-defined crosshairs

SHOW_CENTER = True          # Enable geometric image center indicator

EXPOSURE_US = None          # Camera exposure time [us], None for auto exposure
GAIN_DB = None              # Camera gain [db], None for auto gain



sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(FRAMESIZE)
sensor.set_vflip(False)
sensor.set_hmirror(False)

if GAIN_DB is None:
    sensor.set_auto_gain(True)
else:
    sensor.set_auto_gain(False, gain_db = 0)

if EXPOSURE_US is None:
    sensor.set_auto_exposure(True)
else:
    sensor.set_auto_exposure(False, exposure_us = EXPOSURE_US)



t_start = pyb.micros()
t = 0
t_old = 0


while True:

    img = sensor.snapshot()

    t_old = t
    t = pyb.elapsed_micros(t_start)

    # Draw small cross at image center:
    if SHOW_CENTER:
        img.draw_cross(sensor.width()//2, sensor.height()//2, color=COLOR, size=20)

    # Draw crosshairs at user-defined position:
    if SHOW_CROSSHAIRS:
        img.draw_line(0, CY, sensor.width(), CY, color=COLOR)
        img.draw_line(CX, 0, CX, sensor.height(), color=COLOR)

    # Display FPS:
    img.draw_rectangle(sensor.width()-(2+(9*8)+2), 0, 2+(9*8)+2, 2+10+2, color=0, fill=True)
    img.draw_string(sensor.width()-(9*8)-2, 2, "{:5.1f} FPS".format(1e6/(t-t_old)))

    # Display sensor gain (dB) and exposure time (us):
    img.draw_rectangle(sensor.width()-(2+(9*8)+2), 2+10+2, 2+(9*8)+2, 2+10+10+2, color=0, fill=True)
    img.draw_string(sensor.width()-(9*8)-2, 2+(1*10)+2, "{:6.1f} dB".format(sensor.get_gain_db()))
    img.draw_string(sensor.width()-(9*8)-2, 2+(2*10)+2, "{:6d} us".format(sensor.get_exposure_us()))
