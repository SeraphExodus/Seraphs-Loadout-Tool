import matplotlib.pyplot as plt
import numpy as np
import pyaudio
from scipy import signal
from scipy.io import wavfile

RATE = 48000
CHUNK = 256

p = pyaudio.PyAudio()

player = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, output=True,frames_per_buffer=CHUNK)
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

for i in range()