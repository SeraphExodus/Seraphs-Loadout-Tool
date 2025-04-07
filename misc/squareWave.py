from scipy.io import wavfile
import numpy as np
import matplotlib.pyplot as plt

RATE = 128000
FREQ = 8000
AMP = 20000
DURATION = 0.2

t = np.arange(0,DURATION,1/RATE)
zeroes = np.array([np.int16(0)] * len(t))
data = AMP * np.sin(t*FREQ * 2 * np.pi)

dualchannel = []
formatteddata = []

for i in data:
    formatteddata.append(np.int16(i))

formatteddata = np.array(formatteddata)

wavfile.write("test.wav",RATE,formatteddata)
wavfile.write("zeroes.wav",RATE,zeroes)