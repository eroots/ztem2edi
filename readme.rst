Installs a script to convert ZTEM data in Geosoft .grd or .gdb format to magnetotelluric EDI format.
Call the script from within the folder containing the ZTEM data files to be converted.

Note that the geosoft dependency (and therefore this package) requires python version 3.9.*. Ensure that your environment is using this version before trying to install ztem2edi.

Create a new environment:

  conda create -n ztem2edi python==3.9 pip git

  conda activate ztem2edi

Install the script directly using pip and git:

  pip install git+https://github.com/eroots/ztem2edi.git

Or clone the repository and install using setup.py

  git clone https://github.com/eroots/ztem2edi

  python setup.py install

Install should be performed in a fresh conda environment, as the dependencies require specific versions to work (numpy==1.20, pandas==2.0, python==3.9).

Usage is:
  ztem2edi <.gdb or .grd path> <output_path> <downsample_rate | Default=1000m>

  Specify downsample rate as an integer N will extract every Nth point within the grid as an MT station.

  Alternatively, specify in meters, e.g., 1000m to search for points at a 1000 meter separation

  Meter specification for the downsample rate is not available for .grd files - gdb files preferred as they contain original flight line information.

  Frequency search within .gdb files assumes channels are listed as <component>_<freq>Hz

  Frequency search within .grd files assumes files named as <tag>_<component>_<freq>Hz.grd

Data is converted as follows:

  Tzx = (-1 * XIP) + 1j*XQD
  Tzy = (-1 * YIP) + 1j*YQD

X and Y components are swapped, real and imaginary portions of the vertical magnetic transfer function corresponds to the in-phase and quadrature components of the ZTEM response, respectively.
