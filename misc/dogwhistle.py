import numpy as np
import pyaudio as pa
import wave
import os

def signal_to_wav(signal, fname, Fs):
    """Convert a numpy array into a wav file.

     Args
     ----
     signal : 1-D numpy array
         An array containing the audio signal.
     fname : str
         Name of the audio file where the signal will be saved.
     Fs: int
        Sampling rate of the signal.

    """
    data = (signal * (2 ** 15 - 1)).astype("<h")
    wav_file = wave.open(fname, 'wb')
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(Fs)
    wav_file.writeframes(data)
    wav_file.close()

chunk = 1024
sampleRate=44200
freq = 10000

if os.path.exists('sound.wav'):
    os.remove('sound.wav')

wf = np.array([np.sign(np.sin(freq*2*np.pi*x/sampleRate)) for x in range(sampleRate)])

signal_to_wav(wf,'sound.wav',sampleRate)

wf = wave.open('sound.wav','rb')

p = pa.PyAudio()
stream = p.open(format = 
                p.get_format_from_width(wf.getsampwidth()),
                channels = wf.getnchannels(),
                rate = wf.getframerate(),
                output = True)
data = wf.readframes(chunk)

while data:

    stream.write(data)
    data = wf.readframes(chunk)

wf.close()
stream.close()
p.terminate()

