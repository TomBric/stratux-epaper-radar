#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
#
# BSD 3-Clause License
# Copyright (c) 2020, Thomas Breitbach
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE

import logging
import epd3in7
from PIL import Image, ImageDraw, ImageFont
import math
import time
from pathlib import Path

# global constants
LARGE = 32           # size of height indications of aircraft
SMALL = 24      # size of information indications on top and bottom
VERYSMALL = 18
AIRCRAFT_SIZE = 6        # size of aircraft arrow
MINIMAL_CIRCLE = 20     # minimal size of mode-s circle
# end definitions

# global device properties
sizex = 0
sizey = 0
zerox = 0
zeroy = 0
max_pixel = 0
largefont = ""
smallfont = ""
verysmallfont = ""
device = None
epaper_image = None
# end device globals


def posn(angle, arm_length):
    dx = round(math.cos(math.radians(270+angle)) * arm_length)
    dy = round(math.sin(math.radians(270+angle)) * arm_length)
    return dx, dy


def make_font(name, size):
    font_path = str(Path(__file__).resolve().parent.joinpath('fonts', name))
    return ImageFont.truetype(font_path, size)


def epaper_display():
    global device
    global epaper_image
    device.async_display_1Gray(device.getbuffer(epaper_image))


def epaper_is_busy():
    global device
    return device.async_is_busy()


def oled_init():
    global sizex
    global sizey
    global zerox
    global zeroy
    global max_pixel
    global largefont
    global smallfont
    global verysmallfont
    global device
    global epaper_image

    device = epd3in7.EPD()
    device.init(0)
    device.Clear(0xFF, 0)   # necessary to overwrite everything
    epaper_image = Image.new('1', (device.height, device.width), 255)
    draw = ImageDraw.Draw(epaper_image)
    device.init(1)
    device.Clear(0xFF, 1)
    sizex = device.height
    sizey = device.width
    zerox = sizex / 2
    zeroy = 200    # not centered
    max_pixel = 400
    largefont = make_font("Font.ttc", LARGE)               # font for height indications
    smallfont = make_font("Font.ttc", SMALL)            # font for information indications
    verysmallfont = make_font("Font.ttc", VERYSMALL)  # font for information indications
    # measure time for refresh
    start = time.time()
    # do sync version of display to measure time
    device.display_1Gray(device.getbuffer(epaper_image))
    device.display_1Gray(device.getbuffer(epaper_image))
    end = time.time()
    display_refresh = (end-start) / 2
    logging.info("Measured Display Refresh Time: "+ str(display_refresh)+ " seconds")
    return draw, max_pixel, zerox, zeroy, display_refresh


def cleanup():
    device.init(0)
    device.Clear(0xFF, 0)
    device.sleep()
    device.Dev_exit()
    logging.debug("Epaper cleaned up.")


def centered_text(draw, y, text, font, fill):
    ts = draw.textsize(text, font)
    draw.text((zerox - ts[0] / 2, y), text, font=font, fill=fill)


def oled_startup(draw, target_ip, seconds):
    logo = Image.open('/home/pi/epaper-radar/stratux-logo-192x192.bmp')
    draw.bitmap((zerox-192/2, 0), logo, fill="black")
    centered_text(draw, 193, "EPaper-Radar 1.0", largefont, fill="black")
    centered_text(draw, sizey - VERYSMALL - 2, "Waiting for " + target_ip, verysmallfont, fill="black")
    epaper_display()
    time.sleep(seconds)


def aircraft(draw, x, y, direction, height):
    p1 = posn(direction, 2 * AIRCRAFT_SIZE)
    p2 = posn(direction + 150, 4 * AIRCRAFT_SIZE)
    p3 = posn(direction + 180, 2 * AIRCRAFT_SIZE)
    p4 = posn(direction + 210, 4 * AIRCRAFT_SIZE)

    draw.polygon(((x + p1[0], y + p1[1]), (x + p2[0], y + p2[1]), (x + p3[0], y + p3[1]), (x + p4[0], y + p4[1])),
                 fill="black", outline="black")
    if height >= 0:
        signchar = "+"
    else:
        signchar = "-"
    t = signchar + str(abs(height))
    tsize = draw.textsize(t, largefont)
    if tsize[0] + x + 4 * AIRCRAFT_SIZE - 2 > sizex:
        # would draw text outside, move to the left
        tposition = (x - 4 * AIRCRAFT_SIZE - tsize[0], int(y - tsize[1] / 2))
    else:
        tposition = (x + 4 * AIRCRAFT_SIZE + 1, int(y - tsize[1] / 2))
    draw.rectangle((tposition, (tposition[0] + tsize[0], tposition[1] + tsize[1])), fill="white")
    draw.text(tposition, t, font=largefont, fill="black")


def modesaircraft(draw, radius, height, arcposition):
    if radius < MINIMAL_CIRCLE:
        radius = MINIMAL_CIRCLE
    draw.ellipse((zerox-radius, zeroy-radius, zerox+radius, zeroy+radius), width=3, outline="black")
    arctext = posn(arcposition, radius)
    if height > 0:
        signchar = "+"
    else:
        signchar = "-"
    t = signchar+str(abs(height))
    tsize = draw.textsize(t, largefont)
    tposition = (zerox+arctext[0]-tsize[0]/2, zeroy+arctext[1]-tsize[1]/2)
    draw.rectangle((tposition, (tposition[0]+tsize[0], tposition[1]+tsize[1])), fill="white")
    draw.text(tposition, t, font=largefont, fill="black")


def situation(draw, connected, gpsconnected, ownalt, course, range, altdifference):
    draw.rectangle((0, 0, sizex-1, sizey-1), fill="white")  # for now, clear everything in image
    draw.ellipse((zerox-max_pixel/2, zeroy-max_pixel/2, zerox+max_pixel/2, zeroy+max_pixel/2), outline="black")
    draw.ellipse((zerox-max_pixel/4, zeroy-max_pixel/4, zerox+max_pixel/4, zeroy+max_pixel/4), outline="black")
    draw.ellipse((zerox-2, zeroy-2, zerox+2, zeroy+2), outline="black")

    draw.text((5, 1), str(range)+" nm", font=smallfont, fill="black")
    t = "FL"+str(round(ownalt / 100))
    textsize = draw.textsize(t, verysmallfont)
    draw.text((sizex - textsize[0] - 5, SMALL+10), t, font=verysmallfont, fill="black")

    t = str(altdifference) + " ft"
    textsize = draw.textsize(t, smallfont)
    draw.text((sizex - textsize[0] - 5, 1), t, font=smallfont, fill="black", align="right")

    text = str(course) + '°'
    centered_text(draw, 1, text, smallfont, fill="black")

    if not gpsconnected:
        centered_text(draw, 70, "No GPS", smallfont, fill="black")
    if not connected:
        centered_text(draw, 30, "No Connection!", smallfont, fill="black")
