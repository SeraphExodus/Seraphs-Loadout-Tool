import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.io import wavfile

rate, data = wavfile.read("340audioh.wav")

REFIRE = 0.340
THRESHOLD = max(data.transpose()[0] + data.transpose()[1])/4

#truncate left
on = False
i = 0
while on == False:
    if abs(data[i][0]) > THRESHOLD  or abs(data[i][1]) > THRESHOLD:
        on = True
        start = i-int(rate/20)
    i += 1

data = data[start:]
data = data[:rate*30]

left = []
right = []

for i in data:
    left.append(i[0])
    right.append(i[1])

left = np.array(left)
right = np.array(right)

frequencies, times, spectrogram = signal.spectrogram(right, rate)
freq = spectrogram[20]

time = len(data)/rate

shots = []
i = 1
threshold = 0.1*max(freq)
while i < len(freq):
    if freq[i] > threshold and freq[i-1] < threshold:
        shots.append(i * 30/len(freq))
        i += int(REFIRE * len(freq)/30)
    else:
        i += 1

dels = []
for i in range(1,len(shots)):
    dels.append((shots[i]-shots[i-1]))

print('Average Firing Interval: ' + str(np.round(np.average(dels),5)) + ' ± ' + str(np.round(np.std(dels),5)))
print('Longest Interval: ' + str(np.round(max(dels),5)))
print('Shortest Interval: ' + str(np.round(min(dels),5)))

fractioning = 50

downsampling = fractioning/rate
t = np.arange(0,30,downsampling)

i = 0
datasampled = []
while i < len(data):
    datasampled.append(max(left[i],right[i]))
    i += fractioning
    
plt.subplot(3,1,1).plot(t,datasampled)
plt.title('Raw Sound Data')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')

plt.subplot(3,1,2).plot(np.arange(0,30,30/len(freq)),freq)
plt.subplot(3,1,2).plot(shots,[max(freq)]*len(shots),'ro')
plt.title('Spectral Amplitude (' + str(int(frequencies[20])) + 'Hz)')
plt.xlabel('Time(s)')
plt.ylabel('Amplitude')

plt.subplot(3,1,3).pcolormesh(times, frequencies, np.log10(spectrogram))
plt.title('Spectrogram')
plt.ylabel('Freq (Hz)')
plt.xlabel('Time (s)')

plt.show()