# -*- coding: utf-8 -*-
"""
Script for adding the RMW (radius of maximum wind) to the HURDAT data.
"""

import sys
import subprocess as sp
import pandas as pd
from collections import defaultdict
import numpy as np
import pickle

def main():
    base_name = sys.argv[1]

    repo_dir = sp.Popen(['git', 'rev-parse', '--show-toplevel'], stdout=sp.PIPE).communicate()[0].rstrip().decode("utf-8")

    # Load data
    hurdat_data = repo_dir + "/data/" + base_name + ".txt"
    ext_data = repo_dir + "/data/" + "ebtrk_atlc_1988_2017.txt"

    rmw_data = defaultdict(dict)

    with open(ext_data) as f:
        l = True
        name = ''
        while l:
            l = f.readline().strip().split()
            if(len(l) == 0):
                break

            date, year, ID, rmw = l[2], l[3], l[0], l[8]
            rmw_data[ID][date + '-' + year] = rmw

    for hurr, arr in rmw_data.items():
        rmws = []
        for dt, v in arr.items():
            rmws.append(v)

        # Map values to ints and set '-99' values to nans
        rmws = list(map(int, rmws))
        rmws = [s if s != -99 else np.nan for s in rmws]

        # Interpolate array
        rmws_pd = pd.Series(rmws)
        rmws_interp = rmws_pd.interpolate(limit=len(rmws), limit_direction='both')

        # If all are nans
        if all(np.isnan(s) for s in rmws_interp):
            rmws_interp = [0.]*len(rmws_interp)

        # Reassign to interpolated wind speed values
        for i, (dt, v) in enumerate(arr.items()):
            rmw_data[hurr][dt] = rmws_interp[i]

    # pickle dictionary
    output = open('rmw_data.pkl', 'wb')
    pickle.dump(rmw_data, output)
    output.close()

if __name__ == '__main__':
    main()
