# RSBN-Calculator
A Python script to calculate RSBN parameters using RSBN dataset and waypoint file, and output result to a pdf file. A standalone executable is also available through [Releases](https://github.com/gottomo/RSBN-Calculator/releases). The executable can be compiled using the compile.bat script with pyinstaller. Useful tool for a flight planning and navigation with Tu-134.

Even though a GUI-based RSBN calculator already exists (https://www.avsimrus.com/f/fs2004-utilities-45/rsbn-calculator-version-1-3-10010.html), my motivation for scirpting this was because the pre-existing program causes character encoding issues on my Windows 11 system. Furthermore I wanted a pdf file output in a format similar to the Simbrief PDF format. 

## Features:
- Calculate RSBN parameters using RSBN database (.dat) and Flight Plan file as inputs (use RSBN database included in eg. /Tu-134A-3/rsbn_ussr.dat)
- Great Circle Distance calculations using sphere as approximation
- Calculate distances and remaining distances for each legs in kilometers
- Calculate True and Magnetic Heading for each legs using 2025 World Magnetic Model (WMM)
- Supported Flight Plan formats: FS2004 (.pln), X-Plane 11/12 (.fms)
- Output RSBN parameters on command line, txt file, and pdf file

## Installation:
Download and place the [RSBNCalculator.exe]() in a convenient location.  
Alternatively, place the RSBNCalculator.py in a convenient location.

## Requires:
- RSBN Database from the simulator (eg. /Tu-134A-3/rsbn_ussr.dat)
- Flight Plan Waypoint file with either format: X-Plane 11/12 .fms file or FS2004 .pln file

## How to use:
1. Launch RSBNCalculator.py script or RSBNCalculator.exe executable
2. Navigate to and select RSBN database in the first file explorer window pop-up
3. Navigate to and select Flight Plan file in the second file explorer window pop-up
4. RSBN parameters output will be shown on command line, as well as in txt and pdf files output in the same directory as the script or executable file

## Notes on Output Format and Abbreviations:
The RSBN parameters assigned to each waypoint are the settings needed to navigate to the next waypoint.  
Distances are calculated and output in kilometers.
### Abbreviations:
IMT - Intended Magnetic Track  
ITT - Intended True Track  
DIS - Distance to next waypoint (km)  
RDIS - Remaining distance to the final waypoint (km)

## References:
- https://www.avsimrus.com/f/fs2004-utilities-45/rsbn-calculator-version-1-3-10010.html for sanity-checking calculation results
- https://edwilliams.org/avform147.htm#Math, https://en.wikipedia.org/wiki/Great-circle_navigation, https://en.wikipedia.org/wiki/Spherical_trigonometry#Napier's_rules_for_quadrantal_triangles for concepts and formulas
- https://developer.x-plane.com/article/flightplan-files-v11-fms-file-format/ for understanding X-Plane .fms file format
- https://www.ncei.noaa.gov/products/world-magnetic-model for WMM 2025 coefficient file