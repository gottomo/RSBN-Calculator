import numpy as np
from math import nan
from pywmm import WMMv2
import tkinter as tk
from tkinter import filedialog
from fpdf import FPDF
import sys

# Formulas from wikipedia & https://edwilliams.org/avform147.htm#Math
# Useful wikipedia article: https://en.wikipedia.org/wiki/Great-circle_navigation

def dm_to_dd(d, m):
    # dm_to_dd(degree, minutes)
    # Convert angles in degree and minutes to a decimal degree format
    dd = d + float(m)/60
    return dd

def latlong_to_nvector(lat, long):
    # latlong_to_nvector(latitude, longitude)
    # Convert latitude and longitude (in radians) into a 3-dimensional n-vector
    nvector = np.array([np.cos(lat)*np.cos(long), np.cos(lat)*np.sin(long), np.sin(lat)])
    return nvector

def nvector_to_latlong(nvector):
    # nvector_to_latlong(nvector)
    # Convert the 3-dimensional n-vector into latitude and longitude in radians
    lat = np.mod(np.arctan2(nvector[2], np.sqrt(nvector[0]**2+nvector[1]**2)), 2*np.pi)
    long = np.mod(np.arctan2(nvector[1], nvector[0]), 2*np.pi)
    return [lat, long]

def calc_central_angle(lat1, long1, lat2, long2):
    # calc_central_angle(lattitude1, longitude1, latitude2, longitude2)
    # Takes input latitude and longitudes in degree, and returns Central Angle between the two points in radian
    # Convert input angles to radian
    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    long1 = np.radians(long1)
    long2 = np.radians(long2)
    # Central Angle (This formula is more accurate for shorter distance)
    central_angle=2*np.arcsin(np.sqrt((np.sin((lat1-lat2)/2))**2 + np.cos(lat1)*np.cos(lat2)*(np.sin((long1-long2)/2))**2))
    return central_angle
    
def calc_great_circle_distance(lat1, long1, lat2, long2):
    # calc_great_circle_distance(lattitude1, longitude1, latitude2, longitude2)
    # Calculate great circle distance between the two co-ordinates (in radian)
    # Earth's radius
    r = 6371 #km
    d = r * calc_central_angle(lat1, long1, lat2, long2)
    return d

def calc_azimuth(lat1, long1, lat2, long2):
    # calc_azimuth(lat1, long1, lat2, long2)
    # Take input co-ordinate in radian, and calculate azimuth at point 1 towards point 2
    azimuth = np.mod(np.arctan2((np.cos(lat2) * np.sin(long2-long1)), (np.cos(lat1)*np.sin(lat2) - np.sin(lat1)*np.cos(lat2)*np.cos(long2-long1))), 2*np.pi)
    return azimuth

def calc_true_heading(lat1, long1, lat2, long2):
    # calc_true_heading(lat1, long1, lat2, long2
    # Take input coordinates in decimal degree, and calculate true heading at point 1 in degree
    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    long1 = np.radians(long1)
    long2 = np.radians(long2)
    true_heading = np.degrees(calc_azimuth(lat1, long1, lat2, long2))
    return true_heading

def calc_azimuth2(lat1, long1, lat2, long2):
    # calc_azimuth(lat1, long1, lat2, long2)
    # Take input co-ordinate in degree, and calculate azimuth at point 2
    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    long1 = np.radians(long1)
    long2 = np.radians(long2)
    azimuth = np.mod(np.arctan2((np.cos(lat1) * np.sin(long2-long1)), (-np.cos(lat2)*np.sin(lat1) + np.sin(lat2)*np.cos(lat1)*np.cos(long2-long1))), 2*np.pi)
    return azimuth

def calc_zpu(lat_rsbn, long_rsbn, lat1, long1, lat2, long2):
    # calc_zpu(lat_rsbn, long_rsbn, lat1, long1, lat2, long2)
    # Take input co-ordinates in degree, calculate ZPU true course setting for RSBN panel in degree
    # Convert input angles to radian
    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    lat_rsbn = np.radians(lat_rsbn)
    long_rsbn = np.radians(long_rsbn) 
    long1 = np.radians(long1)
    long2 = np.radians(long2)
    # Azimuth aka true course between P1 and P2 at P1
    azimuth1 = calc_azimuth(lat1, long1, lat2, long2) 

    # Convert waypoints into n-vector
    p1 = latlong_to_nvector(lat1, long1)
    p2 = latlong_to_nvector(lat2, long2)
    rsbn = latlong_to_nvector(lat_rsbn, long_rsbn)
    # Calculate n-vector for points on the course (or its extention) closest to the RSBN station 
    course = p2 - p1
    p1_to_rsbn = rsbn - p1
    rsbn_projection = p1 + np.dot(course, p1_to_rsbn)/np.dot(course, course) * course
    rsbn_projection = nvector_to_latlong(rsbn_projection)
    # To find azimuth at RSBN, calculate azimuth from RSBN to the perpendicular point on the p1-p2 course, then add or subtract 90deg
    azimuth_rsbn_perpendicular = calc_azimuth(lat_rsbn, long_rsbn, rsbn_projection[0], rsbn_projection[1])
    azimuth_diff = np.mod(azimuth1-azimuth_rsbn_perpendicular, 2*np.pi)
    azimuth_rsbn = np.mod(azimuth_rsbn_perpendicular + azimuth_diff, 2*np.pi)
    return np.degrees(azimuth_rsbn)

# Prepare Header and Footer for PDF file output
class PDF(FPDF):
    def header(self):
        # Create page border for every pages
        self.rect(5, 5, 200, 287, 'D')
        self.set_font("Courier", size=14)
        if self.page_no()==1:
            self.cell(0, 5, text="FLIGHT LOG & RSBN SETTINGS", ln=1, align="C")
            self.cell(0, 5, text="--------------------------", ln=1, align="C")
        self.write(6, text="---------------------------------------------------------------\n")
        self.write(6, text="WAYPOINT  IMT  DIS  RSBN STATION       AZIMUTH  ZPU\n")
        self.write(6, text="LAT       ITT RDIS  CHANNEL-IDENT      ORBIT    TGT.ANGLE\n")
        self.write(6, text="LON                 MODE                        TGT.DIS\n")
        self.write(6, text="---------------------------------------------------------------\n")
    def footer(self):
        # Go to 1.5 cm from bottom
        self.set_y(-15)
        # Select Arial italic 8
        self.set_font('Courier', size=14)
        # Print centered page number
        self.cell(0, 10, 'PAGE %s' % self.page_no(), 0, 0, 'C')


# Read & process RSBN Dataset (cis or rsbn)
root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename(title='Select an RSBN Database (rsbn_<era>.dat)')
try:
    # rsbn_era = input("Press 1 to select USSR. Press 2 to select CIS")
    # print(rsbn_era)
    # if rsbn_era==1:
    #     rsbn_dat = open("rsbn_ussr.dat")
    # else:
    #     rsbn_dat = open("rsbn_cis.dat")
    # rsbn_dat = open("rsbn_ussr.dat")
    rsbn_dat = open(file_path)
    [rsbn_channel,rsbn_name,rsbn_ident,rsbn_freq,rsbn_lat,rsbn_long,rsbn_elev_m] = [[], [], [], [], [], [], []]
    for line in rsbn_dat:
        for i, data in enumerate([rsbn_channel,rsbn_name,rsbn_ident,rsbn_freq,rsbn_lat,rsbn_long,rsbn_elev_m]):
            data.append(line.strip().split("|")[i])
    rsbn_dat.close()
    rsbn_lat = [float(lat) for lat in rsbn_lat]
    rsbn_long = [float(long) for long in rsbn_long]
except:
    sys.exit("Failed to read RSBN database. Exiting...")

# Read & process Waypoints
file_path = filedialog.askopenfilename(title='Select a Flight Plan File (FS2004 .pln or X-plane .fms)')
file_extension = file_path.split(".")[-1]
try:
    if file_extension=="pln":
        # For loading FS2004 .pln files
        print("Loading FS2004 .pln flight plan file")
        flight_plan = open(file_path)
        [waypoint_no, waypoint_name, waypoint_lat, waypoint_long] = [[], [], [], []]
        for line in flight_plan:
            if line[:8]=="waypoint":
                waypoint_no.append(int(line.split("=")[0].split(".")[1]))
                waypoint_name.append(line.split(",")[0].split("=")[1])
                waypoint_lat_raw = line.split(",")[2]
                waypoint_lat_d = float(waypoint_lat_raw.split("*")[0][2:])
                waypoint_lat_m = float(waypoint_lat_raw.split("*")[1][1:-1])
                waypoint_lat.append(dm_to_dd(waypoint_lat_d, waypoint_lat_m) * (-1 if waypoint_lat_raw[1]=="S" else 1))
                waypoint_long_raw = line.split(",")[3]
                waypoint_long_d = float(waypoint_long_raw.split("*")[0][2:])
                waypoint_long_m = float(waypoint_long_raw.split("*")[1][1:-1])
                waypoint_long.append(dm_to_dd(waypoint_long_d, waypoint_long_m) * (-1 if waypoint_long_raw[1]=="W" else 1))
        flight_plan.close()
    elif file_extension=="fms":
        # X-Plane .fms file format, for detail refer to https://developer.x-plane.com/article/flightplan-files-v11-fms-file-format/
        print("Loading X-plane .fms flight plan file")
        [waypoint_no, waypoint_name, waypoint_lat, waypoint_long] = [[], [], [], []]
        wp_no = 0
        flight_plan = open(file_path)
        for line in flight_plan:
            line_data = line.split(" ")
            line_prefix = line_data[0]
            if line_prefix=="1" or line_prefix=="2" or line_prefix=="3" or line_prefix=="11" or line_prefix=="28":
                waypoint_no.append(wp_no)
                waypoint_name.append(line_data[1])
                waypoint_lat.append(float(line_data[4]))
                waypoint_long.append(float(line_data[5]))
                wp_no = wp_no+1
        flight_plan.close()
    else:
        print("Unsupported file extension, flight plan not loaded")
except:
    sys.exit("Failed to read waypoint file. Exiting...")

# Loop to go through pairs of waypoints
#   Find true course, magnetic course, great circle distance
#   Find closest RSBN station to the waypoint 1 and select it. If further than max range (160nm?) then skip below steps
#       Check if RSBN station coincides with waypoint 1, if so select "from" mode
#       else if RSBN coincides with waypoint 2, then "to" mode
#       else PRC mode
#       Find Azimuth, Distance, and ZPU

# Acommodate the use of pyinstaller for reading World Magnetic Model (WMM) Coefficients file
try:
    # Path used when ran as executable compiled by pyinstaller
    cof_file = sys._MEIPASS + "/wmm/WMM_2025.COF"
    wmm = WMMv2(coeff_file=cof_file)
except Exception:
    # If using the Python script, use the default 2025 WMM provided by the pywmm module
    wmm = WMMv2()

[true_heading, mag_dec, mag_heading, distance] = [[], [], [], []]
[rsbn_chosen_id, rsbn_mode, rsbn_azimuth, rsbn_orbit, rsbn_zpu, target_angle, target_distance] = [[], [], [], [], [], [], []]
try:
    for waypoint_id in waypoint_no:
        # Calculate Magnetic Declination
        # md = geo_mag.calculate(glat=waypoint_lat[waypoint_id], glon=waypoint_long[waypoint_id], alt=0, time=2025.0).d
        md = wmm.get_declination(waypoint_lat[waypoint_id], waypoint_long[waypoint_id], 2025.0, 0)
        mag_dec.append(md)
        if waypoint_id<len(waypoint_no)-1: # calculate RSBN parameters for all waypoints excluding the last one
            # Calculate the True Heading and Distance between the waypoints
            th = calc_true_heading(waypoint_lat[waypoint_id], waypoint_long[waypoint_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1])
            true_heading.append(th)
            distance.append(calc_great_circle_distance(waypoint_lat[waypoint_id], waypoint_long[waypoint_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1]))
            # Calculate Magnetic Heading
            mag_heading.append(th - md)
            # Calculate the closest RSBN station to the initial WP (wp1)
            rsbn_dist_to_wp1 = []
            for rsbn_id in range(0,len(rsbn_channel)):
                rsbn_dist_to_wp1.append(calc_great_circle_distance(waypoint_lat[waypoint_id], waypoint_long[waypoint_id], rsbn_lat[rsbn_id], rsbn_long[rsbn_id]))
            rsbn_closest_to_wp1_id = np.argmin(rsbn_dist_to_wp1)
            rsbn_closest_to_wp1_dist = min(rsbn_dist_to_wp1)
            # Calculate the closest RSBN station to the final WP (wp2)
            rsbn_dist_to_wp2 = []
            for rsbn_id in range(0,len(rsbn_channel)):
                rsbn_dist_to_wp2.append(calc_great_circle_distance(waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1], rsbn_lat[rsbn_id], rsbn_long[rsbn_id]))
            rsbn_closest_to_wp2_id = np.argmin(rsbn_dist_to_wp2)
            rsbn_closest_to_wp2_dist = min(rsbn_dist_to_wp2)
            # Calculate RSBN parameters: Mode, Azimuth, Orbit, ZPU
            if rsbn_closest_to_wp1_dist < 2 and rsbn_closest_to_wp2_dist < 300:
                # If RSBN station conincides with wp1, use FROM (OT) mode
                rsbn_chosen_id.append(rsbn_closest_to_wp1_id)
                rsbn_mode.append("FROM (OT)")
                rsbn_azimuth.append(calc_true_heading(rsbn_lat[rsbn_closest_to_wp1_id], rsbn_long[rsbn_closest_to_wp1_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1]))
                rsbn_orbit.append(calc_great_circle_distance(rsbn_lat[rsbn_closest_to_wp1_id], rsbn_long[rsbn_closest_to_wp1_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1]))
                rsbn_zpu.append(nan)
                target_angle.append(nan)
                target_distance.append(nan)
            elif rsbn_closest_to_wp2_dist < 2 and rsbn_closest_to_wp1_dist < 300:
                # If RSBN station conincides with wp2, use TO (HA) mode
                rsbn_chosen_id.append(rsbn_closest_to_wp2_id)
                rsbn_mode.append("TO (HA)")
                rsbn_azimuth.append(calc_true_heading(rsbn_lat[rsbn_closest_to_wp2_id], rsbn_long[rsbn_closest_to_wp2_id], waypoint_lat[waypoint_id], waypoint_long[waypoint_id]))
                rsbn_orbit.append(calc_great_circle_distance(rsbn_lat[rsbn_closest_to_wp2_id], rsbn_long[rsbn_closest_to_wp2_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1]))
                rsbn_zpu.append(nan)
                target_angle.append(nan)
                target_distance.append(nan)
            elif rsbn_closest_to_wp1_dist < 300:
                # Use SRP mode using RSBN station closest to WP1
                rsbn_chosen_id.append(rsbn_closest_to_wp1_id)
                rsbn_mode.append("SRP")
                az = calc_true_heading(rsbn_lat[rsbn_closest_to_wp1_id], rsbn_long[rsbn_closest_to_wp1_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1])
                rsbn_azimuth.append(az)
                orb = calc_great_circle_distance(rsbn_lat[rsbn_closest_to_wp1_id], rsbn_long[rsbn_closest_to_wp1_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1])
                rsbn_orbit.append(orb)
                rsbn_zpu.append(calc_zpu(rsbn_lat[rsbn_closest_to_wp1_id], rsbn_long[rsbn_closest_to_wp1_id], waypoint_lat[waypoint_id], waypoint_long[waypoint_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1]))
                target_angle.append(az)
                target_distance.append(orb)
            elif rsbn_closest_to_wp2_dist < 300:
                # Use SRP mode using RSBN station closest to WP2
                rsbn_chosen_id.append(rsbn_closest_to_wp2_id)
                rsbn_mode.append("SRP")
                az = calc_true_heading(rsbn_lat[rsbn_closest_to_wp2_id], rsbn_long[rsbn_closest_to_wp2_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1])
                rsbn_azimuth.append(az)
                orb = calc_great_circle_distance(rsbn_lat[rsbn_closest_to_wp2_id], rsbn_long[rsbn_closest_to_wp2_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1])
                rsbn_orbit.append(orb)
                rsbn_zpu.append(calc_zpu(rsbn_lat[rsbn_closest_to_wp2_id], rsbn_long[rsbn_closest_to_wp2_id], waypoint_lat[waypoint_id], waypoint_long[waypoint_id], waypoint_lat[waypoint_id+1], waypoint_long[waypoint_id+1]))
                target_angle.append(az)
                target_distance.append(orb)
            else:
                # No RSBN station nearby, skip calculation of RSBN parameters
                rsbn_chosen_id.append(-1)
                rsbn_mode.append("")
                rsbn_azimuth.append(nan)
                rsbn_orbit.append(nan)
                rsbn_zpu.append(nan)
                target_angle.append(nan)
                target_distance.append(nan)
                print("No RSBN station nearby")
    # Calculate remaining distance
    remaining_distance=[]
    for waypoint_id in waypoint_no:
        rem_dis=0
        for i in range(waypoint_id, len(waypoint_no)-1):
            rem_dis = rem_dis+distance[i]
        remaining_distance.append(rem_dis)
except:
    sys.exit("An error occured while calculating RSBN parameters. Exiting...")

# Write outputs to terminal & file
print("---------------------------------------------------------------\n")
print("WAYPOINT  IMT  DIS  RSBN STATION       AZIMUTH  ZPU\n")
print("LAT       ITT RDIS  CHANNEL-IDENT      ORBIT    TGT.ANGLE\n")
print("LON                 MODE                        TGT.DIS\n")
print("---------------------------------------------------------------\n")

for waypoint_id in waypoint_no:
    n_or_s = ("N" if waypoint_lat[waypoint_id]>0 else "S")
    e_or_w = ("E" if waypoint_long[waypoint_id]>0 else "W")
    if waypoint_id<len(waypoint_no)-1 and rsbn_chosen_id[waypoint_id] >= 0:
        print(f"\n{waypoint_name[waypoint_id]:<8}  {mag_heading[waypoint_id]:>3.0f} {distance[waypoint_id]:>4.0f}  {rsbn_name[rsbn_chosen_id[waypoint_id]]:<19}{rsbn_azimuth[waypoint_id]:>3.0f}      {rsbn_zpu[waypoint_id]:>3.0f}\n".replace('nan', ''))
        print(f"{n_or_s}{waypoint_lat[waypoint_id]:.4f}  {true_heading[waypoint_id]:>3.0f} {remaining_distance[waypoint_id]:>4.0f}  CH {rsbn_channel[rsbn_chosen_id[waypoint_id]]} - {rsbn_ident[rsbn_chosen_id[waypoint_id]]:<11}{rsbn_orbit[waypoint_id]:>3.0f}      {target_angle[waypoint_id]:>3.0f}\n".replace('nan', ''))
        print(f"{e_or_w}{waypoint_long[waypoint_id]:.4f}            {rsbn_mode[waypoint_id]:<22}      {target_distance[waypoint_id]:>3.0f}\n".replace('nan', ''))
    elif waypoint_id<len(waypoint_no)-1 and rsbn_chosen_id[waypoint_id] == -1:
        print(f"\n{waypoint_name[waypoint_id]:<8}  {mag_heading[waypoint_id]:>3.0f} {distance[waypoint_id]:>4.0f}\n")
        print(f"{n_or_s}{waypoint_lat[waypoint_id]:.4f}  {true_heading[waypoint_id]:>3.0f} {remaining_distance[waypoint_id]:>4.0f}\n")
        print(f"{e_or_w}{waypoint_long[waypoint_id]:.4f}  {distance[waypoint_id]:<8.0f}\n")
    else:
        print(f"\n{waypoint_name[waypoint_id]:<8}\n")
        print(f"{n_or_s}{waypoint_lat[waypoint_id]:.4f}\n")
        print(f"{e_or_w}{waypoint_long[waypoint_id]:.4f}\n")

file = open("RSBN_result_" + waypoint_name[0] + "_" + waypoint_name[-1] + ".txt", "w")
file.write("---------------------------------------------------------------\n")
file.write("WAYPOINT  IMT  DIS  RSBN STATION       AZIMUTH  ZPU\n")
file.write("LAT       ITT RDIS  CHANNEL-IDENT      ORBIT    TGT.ANGLE\n")
file.write("LON                 MODE                        TGT.DIS\n")
file.write("---------------------------------------------------------------\n")

for waypoint_id in waypoint_no:
    n_or_s = ("N" if waypoint_lat[waypoint_id]>0 else "S")
    e_or_w = ("E" if waypoint_long[waypoint_id]>0 else "W")
    if waypoint_id<len(waypoint_no)-1 and rsbn_chosen_id[waypoint_id] >= 0:
        file.write(f"\n{waypoint_name[waypoint_id]:<8}  {mag_heading[waypoint_id]:>3.0f} {distance[waypoint_id]:>4.0f}  {rsbn_name[rsbn_chosen_id[waypoint_id]]:<19}{rsbn_azimuth[waypoint_id]:>3.0f}      {rsbn_zpu[waypoint_id]:>3.0f}\n".replace('nan', ''))
        file.write(f"{n_or_s}{waypoint_lat[waypoint_id]:.4f}  {true_heading[waypoint_id]:>3.0f} {remaining_distance[waypoint_id]:>4.0f}  CH {rsbn_channel[rsbn_chosen_id[waypoint_id]]} - {rsbn_ident[rsbn_chosen_id[waypoint_id]]:<11}{rsbn_orbit[waypoint_id]:>3.0f}      {target_angle[waypoint_id]:>3.0f}\n".replace('nan', ''))
        file.write(f"{e_or_w}{waypoint_long[waypoint_id]:.4f}            {rsbn_mode[waypoint_id]:<22}      {target_distance[waypoint_id]:>3.0f}\n".replace('nan', ''))
    elif waypoint_id<len(waypoint_no)-1 and rsbn_chosen_id[waypoint_id] == -1:
        file.write(f"\n{waypoint_name[waypoint_id]:<8}  {mag_heading[waypoint_id]:>3.0f} {distance[waypoint_id]:>4.0f}\n")
        file.write(f"{n_or_s}{waypoint_lat[waypoint_id]:.4f}  {true_heading[waypoint_id]:>3.0f} {remaining_distance[waypoint_id]:>4.0f}\n")
        file.write(f"{e_or_w}{waypoint_long[waypoint_id]:.4f}  {distance[waypoint_id]:<8.0f}\n")
    else:
        file.write(f"\n{waypoint_name[waypoint_id]:<8}\n")
        file.write(f"{n_or_s}{waypoint_lat[waypoint_id]:.4f}\n")
        file.write(f"{e_or_w}{waypoint_long[waypoint_id]:.4f}\n")

file.close()

pdf = PDF("P", "mm", "A4")
pdf.add_page()
pdf.set_font("Courier", size=14)
for waypoint_id in waypoint_no:
    n_or_s = ("N" if waypoint_lat[waypoint_id]>0 else "S")
    e_or_w = ("E" if waypoint_long[waypoint_id]>0 else "W")
    if waypoint_id<len(waypoint_no)-1 and rsbn_chosen_id[waypoint_id] >= 0:
        if pdf.will_page_break(height=18):
            # Avoid introducing automatic page break mid waypoint
            pdf.add_page()
        pdf.write(6, text=f"\n{waypoint_name[waypoint_id]:<8}  {mag_heading[waypoint_id]:>3.0f} {distance[waypoint_id]:>4.0f}  {rsbn_name[rsbn_chosen_id[waypoint_id]]:<19}{rsbn_azimuth[waypoint_id]:>3.0f}      {rsbn_zpu[waypoint_id]:>3.0f}\n".replace('nan', ''))
        pdf.write(6, text=f"{n_or_s}{waypoint_lat[waypoint_id]:.4f}  {true_heading[waypoint_id]:>3.0f} {remaining_distance[waypoint_id]:>4.0f}  CH {rsbn_channel[rsbn_chosen_id[waypoint_id]]} - {rsbn_ident[rsbn_chosen_id[waypoint_id]]:<11}{rsbn_orbit[waypoint_id]:>3.0f}      {target_angle[waypoint_id]:>3.0f}\n".replace('nan', ''))
        pdf.write(6, text=f"{e_or_w}{waypoint_long[waypoint_id]:.4f}            {rsbn_mode[waypoint_id]:<22}      {target_distance[waypoint_id]:>3.0f}\n".replace('nan', ''))
    elif waypoint_id<len(waypoint_no)-1 and rsbn_chosen_id[waypoint_id] == -1:
        pdf.write(6, text=f"\n{waypoint_name[waypoint_id]:<8}  {mag_heading[waypoint_id]:>3.0f} {distance[waypoint_id]:>4.0f}\n")
        pdf.write(6, text=f"{n_or_s}{waypoint_lat[waypoint_id]:.4f}  {true_heading[waypoint_id]:>3.0f} {remaining_distance[waypoint_id]:>4.0f}\n")
        pdf.write(6, text=f"{e_or_w}{waypoint_long[waypoint_id]:.4f}  {distance[waypoint_id]:<8.0f}\n")
    else:
        pdf.write(6, text=f"\n{waypoint_name[waypoint_id]:<8}\n")
        pdf.write(6, text=f"{n_or_s}{waypoint_lat[waypoint_id]:.4f}\n")
        pdf.write(6, text=f"{e_or_w}{waypoint_long[waypoint_id]:.4f}\n")

pdf.output("RSBN_result_" + waypoint_name[0] + "_" + waypoint_name[-1] + ".pdf")
input("press Enter to exit")