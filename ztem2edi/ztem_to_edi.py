# Converts ZTEM data from Geosoft .grd format to EDI files.
# Note that the .grd data may be interpolated from the actual flight lines, so choose the downsampling rate accordingly.

# Couple of hard-coded values
# Flat error floor to be applied in the EDI file.
flat_error = 0.03
components = ['XIP', 'YIP', 'XQD', 'YQD']
dist_tol = 0.02

from collections import OrderedDict
import numpy as np
import geosoft.gxpy as gxpy
import os
from datetime import datetime
import sys
import pkg_resources


def dd2dms(dd):
    mult = -1 if dd < 0 else 1
    mnt, sec = divmod(abs(dd) * 3600, 60)
    deg, mnt = divmod(mnt, 60)
    return mult * deg, mnt, sec


def to_edi(site, out_file, freqs, info=None, header=None, mtsect=None, defs=None):
    NP = len(freqs)
    lat_deg, lat_min, lat_sec = dd2dms(site['Latitude'])
    long_deg, long_min, long_sec = dd2dms(site['Longitude'])
    default_header = OrderedDict([('ACQBY', '"eroots"'),
                                  ('FILEBY',   '"pyMT"'),
                                  ('FILEDATE', datetime.today().strftime('%m/%d/%y')),
                                  ('LAT', '{:d}:{:d}:{:4.2f}'.format(int(lat_deg), int(lat_min), lat_sec)),
                                  ('LONG', '{:d}:{:d}:{:4.2f}'.format(int(long_deg), int(long_min), long_sec)),
                                  ('ELEV', 0),
                                  ('STDVERS', '"SEG 1.0"'),
                                  # ('PROGVERS', '"ztem2edi {}"'.format(pkg_resources.get_distribution('ztem2edi').version)),
                                  ('COUNTRY', 'CANADA'),
                                  ('EMPTY', 1.0e+32)])
    default_info = OrderedDict([('MAXINFO', 999),
                                ('SURVEY ID', '""')])

    default_defs = OrderedDict([('MAXCHAN', 1),
                                ('MAXRUN', 999),
                                ('MAXMEAS', 9999),
                                ('UNITS', 'M'),
                                ('REFTYPE', 'CART'),
                                ('REFLAT', '{:d}:{:d}:{:4.2f}'.format(int(lat_deg), int(lat_min), lat_sec)),
                                ('REFLONG', '{:d}:{:d}:{:4.2f}'.format(int(long_deg), int(long_min), long_sec))])
    default_mtsect = OrderedDict([('SECTID', '""'),
                                  ('NFREQ', len(site['TZXR'])),
                                  ('HX', '1.01'),
                                  ('HY', '2.01'),
                                  ('HZ', '3.01')])
    if info:
        for key, val in info.items():
            default_info.update({key: val})
    info = default_info
    if header:
        for key, val in header.items():
            default_header.update({key: val})
    header = default_header
    if mtsect:
      for key, val in mtsect.items():
            default_mtsect.update({key: val})
    mtsect = default_mtsect
    if defs:
      for key, val in defs.items():
            default_defs.update({key: val})
    defs = default_defs

    # Write the file
    with open(out_file, 'w') as f:
        f.write('>HEAD\n')
        for key, val in header.items():
            f.write('{}={}\n'.format(key, val))
        f.write('\n')
        
        f.write('>INFO\n')
        for key, val in info.items():
            f.write('{}={}\n'.format(key, val))
        f.write('\n')

        f.write('>=DEFINEMEAS\n')
        for key, val in defs.items():
            f.write('{}={}\n'.format(key, val))
        f.write('\n')
        
        f.write('>=MTSECT\n')
        for key, val in mtsect.items():
            f.write('{}={}\n'.format(key, val))
        f.write('\n')

        f.write('>FREQ //{}\n'.format(NP))
        for freq in freqs:
            f.write('{:>14.4E}'.format(freq))
        f.write('\n\n')

        f.write('>TROT //{}\n'.format(NP))
        for ii in range(NP):
            f.write('{:>14.3f}'.format(0))
        f.write('\n\n')

        f.write('>TXR.EXP //{}\n'.format(NP))
        for ii in range(NP):
            f.write('{:>18.7E}'.format(site['TZXR'][ii]))
        f.write('\n\n')

        f.write('>TXI.EXP //{}\n'.format(NP))
        for ii in range(NP):
            f.write('{:>18.7E}'.format(site['TZXI'][ii]))
        f.write('\n\n')

        f.write('>TYR.EXP //{}\n'.format(NP))
        for ii in range(NP):
            f.write('{:>18.7E}'.format(site['TZYR'][ii]))
        f.write('\n\n')

        f.write('>TYI.EXP //{}\n'.format(NP))
        for ii in range(NP):
            f.write('{:>18.7E}'.format(site['TZYI'][ii]))
        f.write('\n\n')

        f.write('>TXVAR.EXP //{}\n'.format(NP))
        for ii in range(NP):
            f.write('{:>18.7E}'.format(flat_error))
        f.write('\n\n')
        f.write('>TYVAR.EXP //{}\n'.format(NP))
        for ii in range(NP):
            f.write('{:>18.7E}'.format(flat_error))
        f.write('\n\n')

        f.write('>END')


def from_gdb(gdb_path, out_path, downsample_rate, skip_lines=True):
    convert = {'XIP': 'TZXR', 'YIP': 'TZYR', 'XQD': 'TZXI', 'YQD': 'TZYI'}
    data = {'TZXR': [], 'TZYR': [], 'TZXI': [], 'TZYI': [], 'Longitude': [], 'Latitude': []}

    # Open the context like this so you're sure it closes properly afterwards
    if downsample_rate.lower().endswith('m'):
        downsample_distance = float(downsample_rate[:-1])
    else:
        downsample_distance = 0
        skip_rate = int(downsample_rate)

    with gxpy.gx.GXpy() as gxp:
        gdb = gxpy.gdb.Geosoft_gdb.open(gdb_path)
        lines = list(gdb.list_lines(select=False).keys())

        channels = gdb.list_channels()
        freqs = sorted(set([int(x[4:7]) for x in gdb.list_channels() if (x[:3].upper() in components and x.lower().endswith('hz'))]))
        print('Frequency set is: {}'.format(freqs))
        line_skipped = False
        for il, line in enumerate(lines):
            # Do these one at a time just in case they get returned out of order
            if il > 0 and not line_skipped:
                x1, y1 = X[0], Y[0]
            if downsample_distance:
                # Assume the sample distance is constant
                X = gdb.read_line(line, channels='X')[0]
                Y = gdb.read_line(line, channels='Y')[0]
                if skip_lines and il > 0:
                    line_dist = np.min((np.sqrt((x1 - X[0])**2 + (y1 - Y[0])**2),
                                        np.sqrt((x1 - X[-1])**2 + (y1 - Y[-1])**2)))
                    # print(line_dist)
                    # print('Current line separation is: {:>6.2f}'.format(line_dist))
                    if line_dist < downsample_distance - downsample_distance*dist_tol:
                        line_skipped = True
                        continue
                    else:
                        line_skipped = False
                dist = np.sqrt((X[1:] - X[0])**2 + (Y[1:] - Y[0])**2)
                diff = np.diff(dist % downsample_distance, axis=0)
                idx = np.where(diff < 0)[0]
            else:
                idx = np.arange(0, len(X), skip_rate, dtype=int)

            try:
                data['Latitude'] = gdb.read_line(line, channels='Latitude')[0][idx]
                data['Longitude'] = gdb.read_line(line, channels='Longitude')[0][idx]
            except gxpy.gdb.GdbException:
                data['Latitude'] = gdb.read_line(line, channels='Lat')[0][idx]
                data['Longitude'] = gdb.read_line(line, channels='Long')[0][idx]
            for key in data.keys():
                if key not in ('Latitude', 'Longitude'):
                    data.update({key: np.zeros((len(data['Latitude']), len(freqs)))})
            for ii, freq in enumerate(freqs):
                # For some reason it seems to require flipping the real parts
                # print('XIP_{:03d}Hz'.format(freq))
                data['TZYR'][:, ii] = -1 * np.squeeze(gdb.read_line(line, channels='XIP_{:03d}Hz'.format(freq))[0][idx])
                data['TZXR'][:, ii] = -1 *  np.squeeze(gdb.read_line(line, channels='YIP_{:03d}Hz'.format(freq))[0][idx])
                data['TZYI'][:, ii] = np.squeeze(gdb.read_line(line, channels='XQD_{:03d}Hz'.format(freq))[0][idx])
                data['TZXI'][:, ii] = np.squeeze(gdb.read_line(line, channels='YQD_{:03d}Hz'.format(freq))[0][idx])
            
            for ii in range(len(data['TZXR'][:,0])):
                site_name = '{}_{:03d}'.format(line, ii)
                out_file = out_path + site_name + '.edi'
                site = {'Name': site_name,
                        'TZXR': data['TZXR'][ii, :],
                        'TZYR': data['TZYR'][ii, :],
                        'TZXI': data['TZXI'][ii, :],
                        'TZYI': data['TZYI'][ii, :],
                        'Latitude' : data['Latitude'][ii][0],
                        'Longitude' : data['Longitude'][ii][0]}
                out_file = os.path.join(out_path, site_name + '.edi')
                if not os.path.exists(out_path):
                    os.mkdir(out_path)
                to_edi(site, out_file, freqs=freqs, info=None, header=None, mtsect=None, defs=None)


def from_grd(data_path, out_path, downsample_rate):
    files = os.listdir(data_path)
    freqs = set(sorted([int(x[-9:-6]) for x in files if (any(comp in x for comp in components) and x.endswith('Hz.grd'))]))
    for ip, freq in enumerate(freqs):
        for ic, component in enumerate(['XIP', 'YIP', 'XQD', 'YQD']):
            grid_file = '{}{}_{}_{:03d}Hz.grd'.format(grid_path, grid_tag, component, freq)
            grd = hm.load_oasis_montaj_grid(grid_file)
            ds_grd = grd.coarsen(easting=downsample_rate,
                                 northing=downsample_rate,
                                 boundary='trim').mean()
            X, Y = np.meshgrid(ds_grd.easting, ds_grd.northing)
            idx = np.isnan(ds_grd)
            new_lat, new_lon = projection.transform(X, Y)
            if component == 'XIP' and ip == 0:
                all_data = np.zeros((new_lat.size, 4, len(freqs)))
                old_lat, old_lon = new_lat, new_lon
                site_names = [str(ii) for ii in range(len(X.flatten()))]
                site_lats = new_lat.flatten()
                site_lons = new_lon.flatten()
            else:
                if not np.all(np.isclose(new_lat, old_lat)):
                    print('Latitudes differ between grids')
            data[component] = ds_grd.data
            orig_data[component] = grd.data
            
            all_data[:, ic, ip] = data[component].flatten()

    
    for jj, (lat, lon) in enumerate(zip(site_lats, site_lons)):
        site_name = site_names[jj]
        
        if np.any(np.isnan(all_data[jj, :, :])):
            print('Station {} has NaNs. Skipping...'.format(jj))
            continue
        # Report says time dependence is -iwt, so should be flipped if writing to EDI?
        # Apparently not? This setup seems OK, which means the time dependence is already correct and they must have reals reversed?
        # 
        # Is there any rotation in the data?
        d = {'TZYR': -1 * all_data[jj, 0, :],
             'TZXR': -1 * all_data[jj, 1, :],
             'TZYI': all_data[jj, 2, :],
             'TZXI': all_data[jj, 3, :]}

        site_name = '{}_{:03d}'.format(line, ii)
        out_file = out_path + site_name + '.edi'
        site = {'Name': site_name,
                'TZXR': np.squeeze(d['TZXR']),
                'TZYR': np.squeeze(d['TZYR']),
                'TZXI': np.squeeze(d['TZXI']),
                'TZYI': np.squeeze(d['TZYI']),
                'Latitude' : lat,
                'Longitude' : lon}

        out_file = os.path.join(out_path, site_name + '.edi')
        to_edi(site, out_file, freqs=freqs, info=None, header=None, mtsect=None, defs=None)

def main():
    try:
        try:
            downsample_rate = sys.argv[3]
        except IndexError:
            downsample_rate = 10
        if sys.argv[1].endswith('.gdb'):
            from_gdb(gdb_path=sys.argv[1], out_path=sys.argv[2], downsample_rate=str(downsample_rate))
            return
        elif sys.argv[1].endswith('.grd'):
            from_grd(gdb_path=sys.argv[1], out_path=sys.argv[2], downsample_rate=str(downsample_rate))
            return
    except IndexError:
        pass
    print('Usage is:\n')
    print('\t ztem2edi <.grd or .gdb path> <output_path> <downsample_rate | Default=10>\n')
    print('Frequency search within .grd files assynes files named as <tag>_<component>_<freq>Hz.grd\n')
    print('Frequency search within .gdb files assumes channels are listed as <component>_<freq>Hz')

if __name__ == '__main__':
    main()

# plt.figure()
# for ii, comp in enumerate(data.keys()):
#     plt.subplot(2, 2, ii + 1)
#     plt.pcolor(new_lon, new_lat, data[comp], cmap=cm.get_cmap('turbo', N=32, invert=True))
# plt.figure()
# for ii, comp in enumerate(data.keys()):
#     plt.subplot(2, 2, ii + 1)
#     plt.pcolor(orig_data[comp], cmap=cm.get_cmap('turbo', N=32, invert=True))

