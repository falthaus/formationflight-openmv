"""
Testing basic features and behaviour with old 'sensor' module for GRAYSCALE and RGB565
The 'sensor' module is deprecated
The 'pyb' module is deprecated

(C) 2026  Felix Althaus

"""


import sensor
import pyb

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.VGA)
sensor.set_windowing((500, 400))
sensor.set_auto_exposure(False, exposure_us=8000)
sensor.set_auto_gain(False, gain_db=0)


width = sensor.get_windowing()[2]
frame_id = 0
t_start = pyb.micros()
t = 0
t_old = 0


while True:

    img = sensor.snapshot()
    t_old = t
    t = pyb.elapsed_micros(t_start)

    blobs = img.find_blobs([(255, 255)], merge=False)

    for blob in blobs:
        img.draw_rectangle(blob.rect(), color=0)
        img.draw_cross(blob.cx(), blob.cy(), color=0)

    t_exp = sensor.get_exposure_us()

    # Frame ID:
    img.draw_rectangle(0, 6-6, 2+(7*8)+2, 2+(1*10)+2, color=0, fill=True)
    img.draw_string(2, 2+6-6, f"#{frame_id:6d}")

    img.draw_rectangle(width-(2+(9*8)+2), 0, 2+(9*8)+2, 2+10+2+10+2, color=0, fill=True)
    # FPS
    img.draw_string(width-(9*8)-2, 2, f"{1e6/(t - t_old):5.1f} FPS")
    # Exposure [us]
    img.draw_string(width-(9*8)-2, 2+(1*10)+2, f"{t_exp:6d} us")


    t_old = t
    frame_id = (frame_id + 1) % (2**16)
