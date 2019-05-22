#!/usr/bin/env python
#############################################################################
#
#  Program : redate_ancil_dump.py
#  Author  : Neil Massey
#  Date    : 07/01/14
#  Purpose : Functions to redate ancil files or dumps (translated from IDL)
#  Modified: SS modified to redate day (21/02/2019)
#############################################################################

import sys, os, getopt
from read_um import *
from write_ancil import write_ancil
import array
import numpy

#############################################################################

def redate_dump_fixhdr(infile, outfile, day):
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
    
    fix_hdr[29] = day

    for i in range(0, fix_hdr[151]):
        pp_hdrs[i,2] = day
        pp_hdrs[i,8] = day    
    # read all the data in
    data = read_data(fh, fix_hdr, intc, pp_hdrs)
    
    # write out the file
    write_ancil(outfile, fix_hdr, intc, realc, pp_hdrs, data, levc, rowc)
    fh.close()

#############################################################################

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], 'i:o:d:', ['input==', 'output==', 'day=='])
    calendar = "-1"
    periodic = False
    dump = False
    strip_cm = False
    for opt, val in opts:
        if opt in ['--input=','--input', '-i']:
            infile = val
        if opt in ['--output=','--output', '-o']:
            outfile = val
        if opt in ['--day=','--day', '-d']:
	    date = val
    try:
        day = int(date)
    except:
        print "Day in format dd"
        sys.exit(0)

    redate_dump_fixhdr(infile, outfile, day)
