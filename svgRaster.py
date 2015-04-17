#!/usr/bin/python

import Image
import ImageEnhance
import StringIO
import base64
import xml.etree.ElementTree as ET
import re
import sys
import argparse


#####################################
#### DEFAULTS #######################


# This program assumes units are in MM so be sure 
# that setting is in your header
GCODE_HEADER = """
G90
M80
G0F8000
G1F8000
"""

GCODE_FOOTER = """
M81
S0
G0X0Y0F8000
"""
    

MOVE_GCODE = "G0 X%X Y%Y"       # %X, %Y 
BURN_GCODE = "S%S\nG1 X%X Y%Y"  # %X, %Y, %S (laser power)

YHOME = 1   # 1 = TOP, -1 = BOTTOM
XHOME = 1   # 1 = LEFT, -1 = RIGHT 

SVG_DPI = 90            # What DPI is your SVG file?  This is important for positioning.
IMAGE_DPI = 90          # Convert image to this dpi
POWER_MIN = -50         # POWER FOR WHITE
POWER_MAX = 50          # POWER FOR BLACK
NUMCOLORS = 16          # Convert images to this many shades of grey.


#### DEFAULTS #######################
#####################################

parser = argparse.ArgumentParser(usage="%(prog)s [-h] [options] svgfile", description="Find Embedded images in an SVG and convert them to Gcode.")
parser.add_argument('-Y',action='store_true', help="Switch Y axis from default direction")
parser.add_argument('-X',action='store_true', help="Switch X axis from default direction")
parser.add_argument('--svgdpi', type=int, metavar="S", help="DPI of SVG file (Default: "+str(SVG_DPI)+")")
parser.add_argument('--imagedpi',type=int, metavar="I", help="DPI to use when engraving image (Default: "+str(IMAGE_DPI)+")")
parser.add_argument('--min',type=float, metavar="MIN", help="Minimum power value (Default "+str(POWER_MIN)+")")
parser.add_argument('--max',type=float, metavar="MAX", help="Maximum power value (Default "+str(POWER_MAX)+")")
parser.add_argument('--numcolors',type=int, metavar="N", help="Number of colors to use in images (Default: "+str(NUMCOLORS)+")")
parser.add_argument('svgfile')
args = parser.parse_args()

if args.Y:
    YHOME *= -1

if args.X:
    XHOME *= -1

if args.svgdpi:
    SVG_DPI = args.svgdpi

if args.imagedpi:
    IMAGE_DPI = args.imagedpi

if args.min:
    POWER_MIN = args.min

if args.max:
    POWER_MAX = args.max

if args.numcolors: 
    NUM_COLORS = args.numcolors

SVGFILENAME = args.svgfile
DPU = SVG_DPI / 25.4                    # Convert SVG_DPI to MM  
PIXEL_SIZE = 1 / (IMAGE_DPI / 25.4)     # Calculate pixel size in MM based on IMAGE_DPI 


PAGE_WIDTH = 0
PAGE_HEIGHT = 0

def MOVE_TO (x, y):
    print MOVE_GCODE.replace("%X",str(x)).replace("%Y",str(y))

def BURN_TO (x, y, val):
    print BURN_GCODE.replace("%X",str(x)).replace("%Y",str(y)).replace("%S",str(val))

def imageToGcode ( img, x, y, width, height, smin, smax, pixel_size ):
    # Convert image to gcode 

    width = int (width / pixel_size)
    height = int ( height / pixel_size )

    img = img.resize((width, height), Image.ANTIALIAS)
    img = img.convert("L")
    img = img.convert('P',dither=None, palette=Image.ADAPTIVE,colors=NUMCOLORS)
    pixels = list(img.getdata())
    pixels = [pixels[i * width:(i + 1) * width] for i in xrange(height)]

    ycur = y
    xcur = x
    xdir = 1
    POWER_STEP = float((POWER_MAX-POWER_MIN)/float(NUMCOLORS-1))
    for row in pixels:
        lastval = -1
        if xdir < 0:
            row = reversed(row)

        for pixel in row:
            xcur += XHOME * pixel_size * xdir
            sval=0
            if pixel>0:
                sval = pixel * POWER_STEP + POWER_MIN
            if sval > 0:
                if lastval <= 0:
                    MOVE_TO(xcur,ycur)
            if sval != lastval and lastval>0:
                BURN_TO(xcur,ycur,lastval)
            lastval = sval
        if sval>0:
            BURN_TO(xcur,ycur,sval)
        xdir *= -1
        ycur += YHOME * pixel_size
    return None


def getTransitions ( elem, xtrans, ytrans, direction ):
    if "transform" in elem.attrib:
        tre = re.compile('(([a-z]+)\s*\(([^)]*)\))', re.IGNORECASE).findall 
        matches = tre(elem.attrib["transform"])
        for match in matches:
            ttype = match[1].lower()
            if ttype == "translate":
                params = {}
                fre = re.compile('(-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)').findall
                fmatches = fre(match[2])
                for i in range(len(fmatches)):  
                    params[i] = float(fmatches[i])
                if len(params) == 1:
                    xtrans += direction * params[0]
                    ytrans += direction * params[0]
                if len(params) == 2:
                    xtrans += direction * params[0]
                    ytrans += direction * params[1]
    return xtrans,ytrans



def svgToImages ( svgfile ):
    # Look for embedded images in svg file

    global PAGE_WIDTH, PAGE_HEIGHT
    images = [] 
    xtrans = 0
    ytrans = 0
    for (event, elem) in  ET.iterparse( svgfile, events=("start","end") ):
        tag = elem.tag.rpartition('}')[2]

        if event == "start":

            if tag == "svg":
                for k,v in elem.attrib.items():
                  attr = k.rpartition('}')[2].lower()
                  if attr == "width":
                      PAGE_WIDTH = float(v)
                  if attr == "height": 
                      PAGE_HEIGHT = float(v)

            xtrans, ytrans = getTransitions(elem,xtrans,ytrans,1)

        if event == "end":
            if tag == 'image':
                image = {}
                image["x"] = 0.0
                image["y"] = 0.0
                image["h"] = 0
                image["w"] = 0
                image["d"] = ""
                image["mime"] = ""
                image["encoding"] = ""
                for k,v in elem.attrib.items():
                    try:
                        attr = k.rpartition('}')[2].lower()
                        if attr == 'href':
                            dtype,d = v.split(",")
                            dmime,dencode = dtype.split(";")
                            dstart,dmime = dmime.split(":")
                        if dstart == "data":
                           image["d"] = d
                           image["mime"] = dmime
                           image["encoding"] = dencode
                        if attr == 'x':
                            image["x"] = float(v) + xtrans
                        if attr == 'y':
                            image["y"] = float(v) + ytrans
                        if attr == 'height':
                            image["h"] = float(v)
                        if attr == 'width':
                            image["w"] = float(v)
                    except:
                        pass
                images.append(image)

            xtrans, ytrans = getTransitions(elem,xtrans,ytrans,-1)

    return images


images = svgToImages(SVGFILENAME)

for image in images:
    d = StringIO.StringIO(base64.b64decode(image["d"]))
    img = Image.open(d)

    w = float(image["w"] / DPU)
    h = float(image["h"] / DPU)

    if XHOME == 1:
        x = float(image["x"] / DPU)
    else:
        x = float( (PAGE_WIDTH - (image["x"] + image["w"])) / DPU)

    if YHOME == 1:
        y = float(image["y"] / DPU)
    else:
        y = float( (PAGE_HEIGHT - (image["y"] + image["h"])) / DPU)

    print GCODE_HEADER
    imageToGcode( img, x, y, w, h, POWER_MIN, POWER_MAX, PIXEL_SIZE)
    print GCODE_FOOTER
