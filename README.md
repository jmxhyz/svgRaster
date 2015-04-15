# svgRaster

This script looks for images embedded in SVG files and then creates gcode to engrave them in the same location (X,Y) and the same size (Width/Height).


## Usage
```
./svgRaster.py mydesign.svg > mydesign-images.ngc

```

## Gcode

This was created and tested with LasaurApp for Lasersaur so the default gcode settings are for that.  It has successfully worked on a LinuxCNC driven Buildlog 2.x laser by changing the following settings:

```
GCODE_HEADER = """
%
M64 P0 ( M64 OFF/ M62 ON)
G01 Z-0.000001 F10000
(Header)
G21 (All units in mm)
S10000 (PULSERATE) F10000 (FEEDRATE)
"""

GCODE_FOOTER = """
(Footer)
M5 (LOCK)
G53 G0 X0 Y255
M2 (END)
%
"""

MOVE_GCODE = "M5\nG00 X%X Y%Y\nM3"
BURN_GCODE = "M68 E0 Q%S\nM62 P0\nG01 X%X Y%Y Z-0.000001"
POWER_MIN = 0.12
POWER_MAX = 0.17  
```

## Settings

There are several settings to play with here.  The Power Min and Power Max settings need to be changed to match your desired effect and machine.  Setting a Power Min below your fire threshold will cause the script to skip the lighter colors which is sometimes desired.


## Image Processing

There is a lot of information covering this topic on the internet already but I thought I'd give a quick example that is generally a good starting point.

**Using GIMP**

Colors > Levels > Gamma 

*Change the default 1.00 to 3.5*


Filters > Enhance > Unsharp Mask

*Radius: 10*

*Amount: 5.00*

*Threshold 6*

