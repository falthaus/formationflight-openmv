"""
Testing basic features and behaviour with old 'sensor' module.
Both the 'sensor' and the 'pyb' modules are deprecated.

Constraint for the OpenMV H7: using grayscale VGA or WVGA2 without cropping (CROP_FACTOR=1)
is only supported wth custom firmware, otherwise there isn't sufficient memory available.
This custom firmware does not support RGB565 at any resolution.

(C) 2026  Felix Althaus

"""

CROP_FACTOR = 1.0   # 1.0 or lower if full frame size is not supported


import sensor
import pyb


sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.WVGA2)
sensor.set_windowing((int(sensor.width()*CROP_FACTOR),
                      int(sensor.height()*CROP_FACTOR)))
#sensor.set_auto_exposure(False, exposure_us=2000)
sensor.set_auto_gain(False, gain_db=0)


width = sensor.get_windowing()[2]
frame_id = 0
t_start = pyb.micros()
t = 0
t_old = 0


while True:

    img = sensor.snapshot()
    t = pyb.elapsed_micros(t_start)

    blobs = img.find_blobs([(255, 255)], x_stride=2, y_stride=2, merge=False)

    for blob in blobs:
        img.draw_rectangle(blob.rect(), color=0)
        img.draw_cross(blob.cx(), blob.cy(), color=0)

    exposure_us = sensor.get_exposure_us()

    # Frame ID:
    img.draw_rectangle(0, 6-6, 2+(7*8)+2, 2+(1*10)+2, color=0, fill=True)
    img.draw_string(2, 2+6-6, f"#{frame_id:6d}")

    img.draw_rectangle(width-(2+(9*8)+2), 0, 2+(9*8)+2, 2+10+2+10+2, color=0, fill=True)
    # FPS
    img.draw_string(width-(9*8)-2, 2, f"{1e6/(t - t_old):5.1f} FPS")
    # Exposure [us]
    img.draw_string(width-(9*8)-2, 2+(1*10)+2, f"{exposure_us:6d} us")

    t_old = t
    frame_id = (frame_id + 1) % (2**16)
