import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from functools import reduce
import sys, pickle

class HurricaneDatabase():
    ''' This object preprocesses and stores data from the converted model
        data.'''
    def __init__(self):
        self.cyclone_IDs = []
        self.events = {}
        self.data_types = ['date', 'time','latitude', 'longitude', 'max_wind']
        self.valid_times = ['00:00:00', '06:00:00', '12:00:00', '18:00:00']

    def load_data(self, filename):
        ''' Loads raw data from .txt file. Data is stored in 'event' dictionary.
        Data for a particular cyclone is accessed by entering the cyclone ID as a key:
        e.g. data for cyclone with ID '0' is stored in events['0']. '''
        # Read in data
        with open(filename) as f:
            l = f.readline()
            while l:
                # Extract header arguments
                header = [i.strip() for i in l.strip().split(',')]
                cyclone_ID, n = header

                # Add new event
                self.add_event(cyclone_ID)

                # Add event data for each timestamp
                for i in range(int(n)):
                    self.add_entry(cyclone_ID, self.read_row(f.readline()))
                l = f.readline()

                # Set index to datetime
                self.events[cyclone_ID] = self.index_as_date_time(self.events[cyclone_ID])

                # Convert numerical data from str to float
                self.events[cyclone_ID] = self.convert_to_floats(self.events[cyclone_ID])

    def add_event(self, cyclone_ID):
        ''' Adds new key to events dict '''
        # Add event and initialize dataframe
        self.cyclone_IDs.append(cyclone_ID)
        self.events[cyclone_ID] = pd.DataFrame(columns=self.data_types)

    def add_entry(self, cyclone_ID, row):
        ''' Adds new data line for given cyclone ID '''
        # Add row to dataframe
        length = self.events[cyclone_ID].shape[0]
        self.events[cyclone_ID].loc[length] = row

    def read_row(self, row):
        ''' Reads each row and converts to correct datetime format '''
        # Strip out raw data
        data = [entry.strip() for entry in row.strip().split(',')]

        # Datetime conversion
        self.date_time_format(data)
        return data

    @staticmethod
    def date_time_format(data):
        ''' Converts raw datetime data to format recognized by Python '''
        date, time = data[0], data[1]
        data[0] = date[0:4] + "-" + date[4:6] + "-" + date[6:8]
        data[1] = time[0:2] +  ":" + time[2:4] + ":" + "00"
        data[-1] = float(data[-1])
        return data

    def index_as_date_time(self, df):
        ''' Index dataframe by datetime '''
        # Add Datetime index and drop redundant columns
        df['Datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        df = df.drop(['date', 'time'], axis=1)

        # Set index to Datetime and drop left over column
        df = df.set_index(pd.DatetimeIndex(df['Datetime']))
        df = df.drop('Datetime', axis=1)
        return df

    def convert_to_floats(self, df):
        ''' Converts numerical data from str to float '''
        # Convert wind speed, latitude and longitude
        for field in ['max_wind', 'latitude', 'longitude']:
            df[field] = df[field].apply(lambda x: float(x))

        return df

    def event_data(self, cyclone_ID):
        ''' Returns data for a given cyclone ID '''
        return self.events[cyclone_ID]

    def list_events(self):
        ''' Lists all recorded events by cyclone ID '''
        return self.cyclone_IDs

    def datetimes(self):
        ''' Returns all datetimes from start to end at 6 hour intervals '''
        # Start
        t_start = (self.event_data(self.list_events()[0]).head(1).index)[0]

        # End of first cyclone (this will be updated)
        t_end = (self.event_data(self.list_events()[0]).tail(1).index)[0]

        # Loop over events and set final date in season
        for k in range(1, len(self.list_events())):
            t_end_current = (self.event_data(self.list_events()[k]).tail(1).index)[0]
            if t_end_current > t_end:
                t_end = t_end_current

        # Date range in 6 hourly intervals
        drange = pd.date_range(t_start, t_end, freq='6H')

        return drange

    def total_hours(self):
        # Get start and end datetimes of full dataset
        t_start = (self.event_data(self.list_events()[0]).head(1).index)[0]
        t_end   = (self.event_data(self.list_events()[-1]).tail(1).index)[0]

        # Total hours in dataset
        tot_hours = (t_end - t_start).days*24.
        return tot_hours

    def data_range(self, field):
        ''' Determine the max and min values for column '''
        # Set the global max/min values of field to max/min of first event
        events = self.list_events()
        min_v = (self.event_data(events[0])[field]).min()
        max_v = (self.event_data(events[0])[field]).max()

        # Iterate through all events and update global max/min
        for e in self.list_events()[1:]:
            df = self.event_data(e)
            # Check minimum
            if (df[field].min() < min_v):
                min_v = df[field].min()

            # Check maximum
            if (df[field].max() > max_v):
                max_v = df[field].max()

        return min_v, max_v

    def plot_annual_frequency(self,title):
        ''' Bar plot of annual storm frequencies '''
        # Get starting data for each storm
        starting_dates = []
        for event in self.cyclone_IDs:
            storm = self.event_data(event)
            starting_dates.append(storm.index[0].year)

        # Create data frame
        df = pd.DataFrame({'year' : starting_dates})

        # Plot storm frequency per year
        #fig, ax = plt.subplots()
        counts = df['year'].value_counts(sort=False)
        #counts.plot(ax=ax,kind='bar',color='b')

        # Plot average
        #counts_mean = counts.mean()
        #plt.axhline(y=counts_mean, linewidth=3, color='r', linestyle='--')

        # Save and label
        #ax.set_title("Mean = {mean}".format(mean=counts_mean))
        #fig.savefig('{title}_frequency.png'.format(title=title), dpi=600)

        return counts
