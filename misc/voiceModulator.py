import pyaudio
from scipy import signal
import numpy as np

# ------------ Audio Setup ---------------
# constants
CHUNK = 2048 * 2             # samples per frame
FORMAT = pyaudio.paInt16     # audio format (bytes per sample?)
CHANNELS = 1                 # single channel for microphone
RATE = 48000               # samples per second
# Signal range is -32k to 32k
# limiting amplitude to +/- 4k
AMPLITUDE_LIMIT = 4096
GAIN = 2

# pyaudio class instance
p = pyaudio.PyAudio()

# stream object to get data from microphone
stream = p.open(
	format=FORMAT,
	channels=CHANNELS,
	rate=RATE,
	input=True,
	output=True,
	input_device_index=1,
	output_device_index=3,
	frames_per_buffer=CHUNK
)

def bandpass(input,low,high):
    input = np.frombuffer(input, dtype='h')
    fs = RATE
    b, a = signal.butter(6, [low, high], fs=fs, btype='band')
    out = signal.sosfilt(b, a, input)
    return out

def main():
    while True:
        input = stream.read(CHUNK)
        out = bandpass(input, 200, 300)
        stream.write(out)

main()