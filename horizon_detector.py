"""
Horizon detector using adaptive thresholding and linear regression, intended to be used on a UAV.

Inspired by https://github.com/timmarkhuff/horizon_detector


(C) 2026  Felix Althaus

"""

import math
import csi


debug = True    # enable/disable diagnostics (may significantly reduce frame rate)


sensor = csi.CSI()
sensor.reset()
sensor.pixformat(csi.GRAYSCALE)
# TODO: reduce frame size to increase frame rate (about 100 x 100 should be sufficient)
sensor.framesize(csi.QVGA)
#sensor.auto_exposure(False, exposure_us=8000)
sensor.auto_gain(False, gain_db=0)



while True:

    img = sensor.snapshot()

    # Perform thresholding to separate between ground and sky pixels
    # Using Otsu's method: https://en.wikipedia.org/wiki/Otsu's_method
    # Sky pixels will be the ones in the range [otsu_threshold ..  255]
    otsu_threshold = img.get_histogram().get_threshold()

    if debug:
        print(f"Threshold: [{otsu_threshold.value():d} .. 255]")
        # The linear regression algorithm does internal thresholding. To visualise this
        # convert image to binary so it shows in the IDE frame buffer window
        img.binary([(otsu_threshold.value(), 255)])


    # Perform thresholding and linear regression on sky pixels.
    # TODO: Improve robustness by setting area/pixel thresholds
    line = img.get_regression([(otsu_threshold.value(), 255)])


    # The linear regression is done on the sky pixels only, the retuned line is thus not yet
    # the horizon itself. Line y-coordinates have to be doubled to get the estimated horizon.
    # The 'line' object has an angle, theta(), but this is an integer
    # This provides the full resolution angle as float
    if (line.x2()-line.x1()) != 0:
        angle_rad = math.atan(2*(line.y2()-line.y1()) / (line.x2()-line.x1()) )
    else:
        angle_ra = 0

    if debug:
        # Convert to RGB so the estimated horizon is drawn in colour
        img.to_rgb565()
        print(f"Horizon angle: {180/math.pi*angle_rad:.3f} deg")


    # Draw estimated horizon
    # y-coordinates of the linear regression result have to be doubled to get the estimated
    # horizon
    img.draw_line(line.x1(), 2*line.y1(), line.x2(), 2*line.y2(), (255, 0,0))


    if debug:
        print()
