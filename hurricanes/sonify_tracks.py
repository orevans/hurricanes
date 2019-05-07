from read_data import HurricaneDatabase
from cyclone import Cyclone
import matplotlib.pyplot as plt
import numpy as np
import subprocess as sp

def sonify(data, score, fps, sample_rate, field, scale, shift):
    ''' Sonifies all tracks in dataset '''
    print("Sonifying tracks...")
    # Load data
    d = HurricaneDatabase()
    d.load_data(data)

    # Instantiate cyclones and get datetimes
    objs = [Cyclone(d.event_data(e), e) for e in d.list_events()]

    # Get datetimes
    date_times = d.datetimes()

    # Loop through datetimes
    for k, dt in enumerate(date_times):
        for obj in objs:
            if(obj.datetime()[0] == dt):
                start = float(k)/(sample_rate*fps)
                obj.write_to_cmixscore(score, start, fps, sample_rate, scale, shift, field)
