Installs a script to convert ZTEM data in Geosoft .grd or .gdb format to magnetotelluric EDI format.
Call the script from within the folder containing the ZTEM data files to be converted.

Usage is:
  ztem2edi <.grd or .gdb path> <output_path> <downsample_rate | Default=10>

  Specify downsample rate as an integer N will extract every Nth point within the grid as an MT station.

  Alternatively, specify in meters, e.g., 1000m to search for points at a 1000 meter separation

  Frequency search within .grd files assumes files named as <tag>_<component>_<freq>Hz.grd

  Frequency search within .gdb files assumes channels are listed as <component>_<freq>Hz
