from read_data import HurricaneDatabase
import matplotlib.pyplot as plt
import numpy as np
from scipy import interpolate as interp
import matplotlib as mpl

class Cyclone():
    def __init__(self, df, ID, wind_range=None, figure=None, mNotes=None):
        self.df = df
        self.ID = ID
        self.mNotes = mNotes
        self.current_index = 0
        self.fade = 1.0
        self.lats = []
        self.longs = []

        self.catastrophic = False
        if float(df['max_wind'].max()) > 137.0:
            self.catastrophic = True

        if wind_range is not None:
            self.wind_range = wind_range


        self.tracks = None
        self.layer_thresholds = {'34.0':0.9, '64.0':0.8, '83.0':0.7,\
                                 '96.0': 0.6, '113.0':0.5, '137.0':0.4}

    def pan(self):
        ''' Pan according to longitude (currently stereo) '''
        # O is right, 1 is left
        return "0.5"

    def datetime(self):
        ''' Returns datetimes for cyclone '''
        return self.df.index

    def duration(self):
        ''' Returns duration of cyclone '''
        return float(len(self.df.index))

    def event_data(self):
        ''' Returns cyclone data '''
        return self.df

    def color_scale(self, current_wind):
        ''' Normalizes color map reference to be between 0 and 1. This colormap
        describes the max sustained windspeed '''
        min_wind, max_wind = self.wind_range[0], self.wind_range[1]
        return (current_wind - min_wind)/(max_wind - min_wind)

    def update_track(self, dt, figure):
        ''' Updates path location and color for cyclone at time t '''
        # Set initial latitude/longitude
        if(len(self.lats) == 0):
            self.lats.append(self.df['latitude'][dt])
            self.longs.append(self.df['longitude'][dt])
            self.current_index += 1

        else:
            # Update latitude/longitudes
            lats_prev, longs_prev = self.lats[-1], self.longs[-1]
            self.lats.append(self.df['latitude'][dt])
            self.longs.append(self.df['longitude'][dt])
            lats_new, longs_new = self.df['latitude'][dt], self.df['longitude'][dt]

            # Uodate location in plot
            self.tracks[self.current_index].set_data(figure([longs_prev,\
                                            longs_new], [lats_prev, lats_new]))

            # Set new color (according to max windpseed)
            col_index = self.color_scale(self.df['max_wind'][dt])
            self.tracks[self.current_index].set_color(plt.cm.jet(col_index))

            # Not sure about this
            self.tracks[self.current_index].set_linewidth(9.)

            self.current_index += 1

    def set_figure(self, figure):
        #self.figure = figure
        self.tracks = [(figure.plot([], [], alpha=self.fade))[0] for k in range(len(self.df.index))]

    def initialize_cyclone(self, t, figure):
        ''' Sets initial location/radius for cyclone '''
        # Initial location and color
        x, y = figure(self.df['longitude'][t], self.df['latitude'][t])
        col_index = self.color_scale(self.df['max_wind'][t])

    def remove_inactive(self, fade_inc, figure):
        ''' Plots progressively faded final state of inactive cyclone.
        The fade period is set by the fade_inc parameter. '''

        # Fade tracks
        for i in range(len(self.tracks)):
            (self.tracks)[i].set_alpha(self.fade)

        #self.date_time.set_alpha(self.fade)
        #if not self.catastrophic:
        if self.fade > 0.1:
            self.fade -= fade_inc

        # Remove tracks if alpha falls below threshold
        if(self.fade < 1.e-2):
            self.lats, self.longs = [], []
            for i in range(len(self.tracks)):
                (self.tracks)[i].set_data(figure(self.longs, self.lats))

    def layer_score_data(self, times, key, field):
        ''' Obtain times and field data for when field exceeds threshold.
        These times may form disjoint intervals '''
        layer_on, i = False, 0
        start_times, end_times, layer_notes = [], [], []
        while(i < len(times)):
            if(self.df[field][i] >= float(key)):
                layer_on = True
                start_times.append(times[i])
                layer_notes_current = []
                while(layer_on == True):
                    if(self.df[field][i] < float(key)):
                        if(len(layer_notes_current) != 1):
                            # Exclude cases w
                            end_times.append(times[i])
                            layer_notes.append(layer_notes_current)
                        else:
                            start_times = start_times[:-1]
                        layer_on = False
                    else:
                        layer_notes_current.append(self.df[field][i])
                        if(i == len(times) - 1):
                            end_times.append(times[i])
                            layer_notes.append(layer_notes_current)
                            break
                        i += 1
                if(i == len(times) - 1):
                    break
            else:
                i += 1

        return start_times, end_times, layer_notes

    def add_score_layer(self, score, start, dur, notes, key):
        ''' Add granular synth layer based on wind speed '''
        notes_scaled = np.asarray(notes)*self.layer_thresholds[key]
        cmix_pitches = self.pitch_cmixline(notes_scaled)

        # Check that length of notes is > 1
        if(len(notes) > 1):
            score.write("GRANSYNTH(%s, %s, amp*6000, wave, granenv, hoptime,\
            hopjitter, mindur, maxdur, minamp, 0.7*maxamp, %s,\
            transpcoll, pitchjitter, 14, %s, %s)\n" \
            % (start, dur, cmix_pitches, self.pan(), self.pan()))

    def set_audio_data(self, start, fps, sample_rate, scale, shift, field):
        ''' Determines audio start time and duration (in seconds) for cyclone,
        and transforms raw data to apporpriate pitches '''
        times = [start + i/(fps*sample_rate) for i in range(len(self.df.index))]
        dur_audio = times[-1] - times[0]
        data_scaled = self.df[field]*scale + shift
        #if(len(times) < 2):
        #    print("FUCKK", times, self.ID)
        return dur_audio, times, data_scaled

    def pitch_cmixline(self, data):
        ''' Converts array to list of pitches to be read by RTCMix. '''
        indexes = np.arange(len(data))
        cmixline = np.zeros(2*len(data))
        cmixline[1::2] = data
        cmixline[0:-1:2] = indexes
        pitches = str(cmixline.tolist()).strip('[').strip(']')
        pitch_cmd = "maketable(\"line\", \"nonorm\", 1000, " + pitches + ')\n'
        return pitch_cmd

    def write_to_cmixscore(self, score, start, fps, \
                            sample_rate, scale, shift, field):
        ''' Adds GRANSYNTH instrument. Uses parameters from audio_data. '''
        audio_data = self.set_audio_data(start, fps, sample_rate, scale, shift, field)
        dur, times, pitches = audio_data
        start = times[0]
        cmix_pitches = self.pitch_cmixline(pitches)

        # Write the base layer
        score.write("GRANSYNTH(%s, %s, amp*6000, wave, granenv, hoptime,\
        hopjitter, mindur, maxdur, minamp, 0.7*maxamp, %s,\
        transpcoll, pitchjitter, 14, %s, %s)\n" % (start, dur, cmix_pitches, self.pan(), self.pan()))

        # Loop through to determine layers
        for key in self.layer_thresholds:
            starts, ends, l_notes = self.layer_score_data(times, key, field)
            durs = np.asarray(ends) - np.asarray(starts)

            # Add each layer to the cmix score
            for k, t in enumerate(starts):
                l_notes[k] = np.asarray(l_notes[k])*scale + shift
                self.add_score_layer(score, t, durs[k], l_notes[k], key)
