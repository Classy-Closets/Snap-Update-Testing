
import sys
import os

from snap import closets

if __name__ == "__main__":
    # cos_xml = sys.argv[1]
    cos_xml = "C:/Users/KenCook/Desktop/test_xml.xml"
    closets.project_pricing.calculate_project_price(cos_xml, True)
