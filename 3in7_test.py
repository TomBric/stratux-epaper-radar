#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd3in7
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

logging.basicConfig(level=logging.ERROR)

try:
    logging.info("epd3in7 Demo")
    
    epd = epd3in7.EPD()
    logging.info("init and Clear")
    epd.init(0)
    epd.Clear(0xFF, 0)
    
    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    font18 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18)
    font36 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 36)
    
    # partial update, just 1 Gary mode
    logging.info("5.show time, partial update, just 1 Gary mode")
    epd.init(1)         # 1 Gary mode
    epd.Clear(0xFF, 1)
    time_image = Image.new('1', (epd.height, epd.width), 255)
    time_draw = ImageDraw.Draw(time_image)
    num = 0
    while (True):
        time_draw.rectangle((10, 10, 200, 80), fill = 255)
        time_draw.text((10, 10), time.strftime('%H:%M:%S'), font = font36, fill = 0)
        epd.display_1Gray(epd.getbuffer(time_image))
        
        num = num + 1
        if(num == 500):
            break
            
    logging.info("Clear...")
    epd.init(0)
    epd.Clear(0xFF, 0)
    
    logging.info("Goto Sleep...")
    epd.sleep()
    epd.Dev_exit()
    
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd3in7.epdconfig.module_exit()
    exit()
