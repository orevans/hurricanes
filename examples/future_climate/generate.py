import sys, time, gc
sys.path.insert(0, '/Users/owenevans/Desktop/hurricanes/hurricanes')

from read_data import HurricaneDatabase
from cyclone import Cyclone
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import matplotlib.animation as manimation
from matplotlib.animation import FFMpegWriter
import animate_tracks as at
import sonify_tracks as st
import subprocess as sp

plt.rcParams['axes.facecolor']='black'
plt.rcParams['savefig.facecolor']='black'

# Set up file writer
fig = plt.figure()
fig.set_size_inches(28.2, 32.4, forward=True)
fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
FFMpegWriter = manimation.writers['ffmpeg']
metadata = dict(title='Movie Test', artist='Matplotlib',
                comment='Movie support!')
writer = FFMpegWriter(fps=600, bitrate=100000000)#80000000)

# Set up figure
#m = Basemap(llcrnrlon=-110.,llcrnrlat=-15.,urcrnrlon=20.0,urcrnrlat=57.,
#            projection='lcc',lat_1=20.,lat_2=40.,lon_0=-60.,
#            resolution ='l')
print("loading basemap...")
m = Basemap(llcrnrlon=-120.,llcrnrlat=-7.,urcrnrlon=-7.0,urcrnrlat=52.,
            projection='lcc',lat_1=1.,lat_2=1.,lon_0=-1.,
            resolution ='l')

print("loading blue marble...")
m.bluemarble()
print("Done...")

# Parameters
sample_rate = 10.
fps = 600.
fade_inc = 0.005
base_name = sys.argv[1]

# Path to data directory
repo_dir = sp.Popen(['git', 'rev-parse', '--show-toplevel'], stdout=sp.PIPE).communicate()[0].rstrip().decode("utf-8")
data = repo_dir + "/data/atl_models/" + base_name + ".txt"

scale, shift = 0.04, 2.2

# Set up RTCMix score
score_name = base_name + ".sco"
f_out = open("./" + score_name , 'w')
f_out.write("set_option(\"clobber = on\")")
f_out.write("rtsetparams(44100, 2)\n")
f_out.write("reset(44100)\n")
f_out.write("load(\"GRANSYNTH\")\n")

output_string = 'rtoutput(\"' + base_name + '.wav\")\n'
f_out.write(output_string)

f_out.write("amp = maketable(\"line\", 1000, 0,0, 1,1, 2,0.5, 3,1, 4,0)\n")
f_out.write("wave = maketable(\"wave\", 2000, 1, 0, 1, 0, 1, 0, 1, 0)\n")
f_out.write("granenv = maketable(\"window\", 2000, \"hanning\")\n")
f_out.write("hoptime = maketable(\"line\", \"nonorm\", 1000, 0,0.01, 1, \
                                0.002, 2,0.05)\n")
f_out.write("hopjitter = 0.0001\n")
f_out.write("mindur = .04\n")
f_out.write("maxdur = .06\n")
f_out.write("minamp = maxamp = 1\n")
f_out.write("transpcoll = maketable(\"literal\", \"nonorm\", 0, 0, .02,\
                                .03, .05, .07, .10)\n")
f_out.write("pitchjitter = 1\n")

# Animate and sonify tracks
data_rcp = data
#at.animate(data, data_rcp, m, writer, sample_rate, fade_inc, base_name)
st.sonify(data, f_out, fps, sample_rate, 'max_wind', scale, shift)
f_out.close()

# Send score to RTCMix
cmix_cmd = 'CMIX < ' + score_name
runCMIX = sp.Popen(cmix_cmd, shell=True)
runCMIX.wait()

# Generate movie
movie_name = base_name + '.mp4'
sound_name = base_name + '.wav'
movie_snd_name = base_name + 'sound.mp4'

# Stich together with ffmpeg
#run_ffmpeg_cmd = 'ffmpeg -i ' + sound_name + ' -i ' + movie_name + ' -c copy ' + movie_snd_name
run_ffmpeg_cmd = 'ffmpeg -i ' + movie_name + ' -i ' + sound_name + ' -c:v copy -c:a aac -strict experimental ' + movie_snd_name

make_movie = sp.Popen(run_ffmpeg_cmd, shell=True)
make_movie.wait()
