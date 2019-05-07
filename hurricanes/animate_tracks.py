from read_data import HurricaneDatabase
from cyclone import Cyclone
import matplotlib.pyplot as plt
import numpy as np
import os

def animate(data, data_rcp, figure, writer, sample_rate, fade_inc, base_name):
    ''' Plots all tracks in dataset '''
    # Read in data
    print("Loading data...")
    d = HurricaneDatabase()
    d.load_data(data)

    d_rcp = HurricaneDatabase()
    d_rcp.load_data(data_rcp)

    # Plot storm frequency
    #d.plot_annual_frequency(base_name)

    # Find range for max wind speed
    wind_range_rcp = list(d_rcp.data_range("max_wind"))
    wind_range = list(d.data_range("max_wind"))

    #print(wind_range)
    min_wind, max_wind = wind_range[0], wind_range[1]
    if wind_range_rcp[1] > max_wind:
        wind_range[1] = wind_range_rcp[1]
    if wind_range_rcp[0] < min_wind:
        wind_range[0] = wind_range_rcp[0]


    # Get events and datetime range
    date_times = d.datetimes()

    # Array contains acurrent active/inactive cyclones
    active_cyclones, inactive_cyclones = [], []

    # Container of Cyclone objects
    objs = [Cyclone(d.event_data(e), e, wind_range) for e in d.list_events()]

    # Initialize empty annotation
    date_time = plt.annotate('', xy=(0, 1), xycoords='axes fraction')

    # Loop through time and add tracks
    print("Animating tracks...")
    with writer.saving(plt.gcf(), base_name + '.mp4', 100):
        for k, dt in enumerate(date_times):
            print(dt)

            # Extract date for annotation
            date = str(dt).split(' ')[0]

            # Update datetime annotation
            date_time.remove()
            date_time = plt.annotate('{dt}'.format(dt=date), xy=(0.05, 0.05),
                                     xycoords='axes fraction', fontsize=160,
                                     color='whitesmoke')
                                     # 180 fontsize
            # Remove tracks for inactive cyclones
            inactive_current = [c for c in active_cyclones if c.datetime()[-1] < dt]
            inactive_cyclones += inactive_current
            inactive_cyclones = [c for c in inactive_cyclones if c.__dict__['fade'] >= 0.0]

            for cyclone in inactive_cyclones:
                cyclone.remove_inactive(fade_inc,figure)

            # Remove old cyclones
            active_cyclones = [c for c in active_cyclones if c.datetime()[-1] >= dt]

            # Add new cyclones
            for obj in objs:
                if (obj.datetime()[0] == dt):
                    obj.set_figure(figure)
                    obj.initialize_cyclone(dt,figure)
                    active_cyclones.append(obj)

            # Update locations
            for cyclone in active_cyclones:
                cyclone.update_track(dt,figure)

            # Add frame to animation
            if((k % sample_rate == 0)):
                writer.grab_frame()
