#!/home/boinc/miniconda2/envs/oifs_pyenv/bin/python
#!/usr/bin/env python
#############################################################################
#
#  Program : perturb_dump.py
#  Author  : Sarah Sparrow
#  Date    : 27/03/19
#  Purpose : Functions to add a perturbation to dump data
#
#############################################################################

import sys, os, getopt
from read_um import *
from write_ancil import write_ancil
import array
import numpy
from netCDF4 import Dataset as netcdf_file

def get_pert_data_nc(pert_file,sf):
    nc_file = netcdf_file(pert_file,'r')
    pert_var=nc_file.variables['perturbation']
    pert=pert_var[:]
    data=pert.flatten()
    print(numpy.max(data))
    print(data.shape)
    # Apply the scaling factor
    data_sf=data*float(sf)
    print(numpy.max(data_sf))
    print(data_sf.shape)
    return data_sf

def get_pert_data(pert_file,sf):
    # read the file as a binary file
    fh = open(pert_file, 'rb')
    fix_hdr = read_fixed_header(fh)
    pp_hdrs = read_pp_headers(fh, fix_hdr)
    intc = read_integer_constants(fh, fix_hdr)
    realc = read_real_constants(fh, fix_hdr)
    if fix_hdr[109] > 1:
        levc = read_level_constants(fh, fix_hdr)
    else:
        levc = numpy.zeros([0],'f')
    if fix_hdr[114] > 1:
        rowc = read_row_constants(fh, fix_hdr)
    else:
        rowc = numpy.zeros([0], 'f')

    # read all the data in
    data_raw = read_data(fh, fix_hdr, intc, pp_hdrs)
    data = array.array('f')
    data.fromstring(data_raw)
    print(data[0:10])
    # Apply the scaling factor
    data_sf=data*float(sf)
    print(numpy.max(data_sf))
    print(data_sf.shape)
    return data_sf

def perturb_data(fh, fix_hdr, intc, pp_hdrs, pert_data,field,start_idx=-1, n_fields=-1):
    if start_idx == -1:
        start_idx = 0
    if n_fields == -1:
        n_fields = pp_hdrs.shape[0]
    field=int(field)
    # read the data as a numpy array
    # get the data size from the integer constants
    pp_hdr_size = fix_hdr[150]
    # calculate the start of the data - the start index multiplied by the
    # sector size - we get the sector size from the pp hdr of the start idx
    sector_size = pp_hdrs[start_idx, 29]
    # loop over the pp headers and get the start location for each field
    # from the pp header
    all_data = array.array('f')
    fidx=0
    for i in range(start_idx, start_idx + n_fields):
        # get where the field starts as an offset in the file
        c_hdr = pp_hdrs[i]
        stash_code=c_hdr[41]
        surface_offset = c_hdr[28]
        surface_size = c_hdr[29]
        data_size = c_hdr[14]
        # seek and write
        fh.seek(surface_offset * WORDSIZE, os.SEEK_SET)
        data_raw = fh.read(surface_size * WORDSIZE)
        data = array.array('f')
        data.fromstring(data_raw)
        if field==stash_code:
            #print(field,stash_code)
            start_fidx=fidx*c_hdr[14]
            end_fidx=start_fidx+c_hdr[14]
            if end_fidx<=len(pert_data):
                old_data=data[0:c_hdr[14]]
                new_data=[sum(x) for x in zip(old_data, pert_data[start_fidx:end_fidx])]
                #print(old_data[0:5],pert_data[start_fidx:(start_fidx+5)],new_data[0:5])
                fidx=fidx+1
            else:
                new_data=data[0:c_hdr[14]]  
        else:
            new_data=data[0:c_hdr[14]]
        all_data.extend(new_data)
    return numpy.array(all_data, 'f')


#############################################################################

def perturb_dump(infile, pert_file, field, outfile,generic,sf):
    sfx=pert_file.split(".")[-1]
    print(sfx)
    if sfx=="nc":
        pert_data=get_pert_data_nc(pert_file,sf)
    else:
        pert_data=get_pert_data(pert_file,sf)

    # read the file as a binary file
    fh = open(infile, 'rb')
    fix_hdr = read_fixed_header(fh)
    pp_hdrs = read_pp_headers(fh, fix_hdr)
    intc = read_integer_constants(fh, fix_hdr)
    realc = read_real_constants(fh, fix_hdr)
    if fix_hdr[109] > 1:
        levc = read_level_constants(fh, fix_hdr)
    else:
        levc = numpy.zeros([0],'f')
    if fix_hdr[114] > 1:
        rowc = read_row_constants(fh, fix_hdr)
    else:
        rowc = numpy.zeros([0], 'f')
    
    # Check if year should be made generic
    if generic == 1:
        fix_hdr[27] = 0

    # read all the data in
    data = perturb_data(fh, fix_hdr, intc, pp_hdrs,pert_data,field)
    
    # write out the file
    write_ancil(outfile, fix_hdr, intc, realc, pp_hdrs, data, levc, rowc)
    fh.close()
    return True

#############################################################################
def main():
    opts, args = getopt.getopt(sys.argv[1:], 'i:p:f:o:g:s', ['input==', 'pert_file==', 'field==', 'output==','generic=','scale_factor='])
    for opt, val in opts:
        if opt in ['--input=','--input', '-i']:
            infile = val
        if opt in ['--pert_file=','--pert_file', '-p']:
            pert_file = val
        if opt in ['--field=','--field', '-f']:
            field = int(val)
        if opt in ['--output=','--output', '-o']:
            outfile = val
        if opt in ['--generic', '-g']:
            generic = 1
        else:
            generic = 0
        if opt in ['--scale_factor=','--scale_factor', '-s']:
            sf = val

    ok=perturb_dump(infile, pert_file, field, outfile,generic,sf)

if __name__ == "__main__":
    main()
