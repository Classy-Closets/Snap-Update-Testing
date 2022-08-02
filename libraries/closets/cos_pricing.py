
import sys
import os

from snap import closets

###    blender --background --python myscript.py cosxml.xml   ###

# <blender> is the path to the blender.exe for a SNaP installation.
# <--background> is the command to run Blender in the background
# <--python> is the command to run the given python script
# <myscript.py> is the path to a python file to run when starting SNaP in the background. 
#               This will be the driver script for whatever operations you would like to carry out for pricing.
# <cosxml.xml> is the xml argument that will be passed into SNaP to request pricing.


if __name__ == "__main__":
    cos_xml = sys.argv[4]
    # cos_xml = "path/to/xml_file"
    closets.project_pricing.calculate_project_price(cos_xml, True)
