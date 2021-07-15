'''
Small script used to calibrate a microphone using a comparison method.
The first microphone is considered as calibrated, and the second is considered to be calibrated.
We use farina's method to determine the transfer function of our microphone
Different methods will be used
Input 1 is the calibrated microhpone
Input 2 is the uncalibrated microphone
'''

# Print iterations progress
def progressBar(iterable, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function
    def printProgressBar (iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()

#%%
EXCEL_VISUALISATION = True
import measpy as mp
import matplotlib.pyplot as plt
from measpy import audio
from measpy.ni import ni_run_measurement, ni_get_devices
from numpy.lib.function_base import average
plt.style.use('seaborn')
import time
import numpy as np
import os
import csv

script_dir = os.path.dirname(os.path.realpath(__file__))

#%%

out_signal_frequencies = [20,20000]

#%%
# First create a measurement
# We send a logsweep signal to use Farina's method
calibration_mesurement = mp.Measurement(out_sig="logsweep",
                    fs = 44100,
                    in_map=[1,2],
                    out_map=[1],
                    out_desc=['Out1'],
                    out_dbfs=[1.0],
                    in_desc=['Calibrated mic','Uncalibrated mic'],
                    in_cal=[0.1,0.1], #Depends on the mic amp you are using. I use 100mV/Pa for amplifying the signal
                    in_unit=['Pa','Pa'],
                    in_dbfs=[1.0,1.0],
                    extrat=[0,0],
                    dur=5,
                    in_device='myDAQ1',
                    out_device='myDAQ1',
                    out_amp=1.0,
                    io_sync = False,
                    out_sig_freqs = out_signal_frequencies
                    )

print("Launching measurement...")
ni_run_measurement(calibration_mesurement)

axes_calibration = calibration_mesurement.plot()
print("Measurement done!")
plt.show() #Check the data

spectrum = calibration_mesurement.tfe() #Convert to transfer function



calibrated_mic_tf = spectrum["In1"]
uncalibrated_mic_tf = spectrum['In2']

calibrated_mic_tf.plot()
plt.show()
#%%

# To format the results we divide the spectrum into bands
# 
def calculate_band_frequencies(number_of_band_per_octave=3) :
    factor = np.power(2, 1/number_of_band_per_octave)
    f_center = 1000
    while f_center > 20:
        f_center =f_center / factor
    frequencies = []
    while f_center < 20000:
        
        frequencies.append(int(np.round(f_center)))
        f_center = f_center * factor
    #We add 20000 for convenience 
    frequencies.append(20000)
    return frequencies



#%%


print("Writing CSV Data...\n")
#Write to a csv file the different values 

#Create the header
headers = ['frequency (Hz)', 'value calibrated mic (dB)', 'value uncalibrated mic (dB)', 'absolute variation (%)', 'gain factor']

#Add data to the csv



with open(f"{script_dir}\\res_calibration{str(time.time())}.csv", "w", encoding='UTF8', newline='') as csv_output:
    writer = csv.writer(csv_output,  dialect='excel')
    writer.writerow(headers)
    number_of_indexes = len(calibrated_mic_tf.freqs)
    print(f"Number of indexes : {number_of_indexes}")
    index_band = 0
    sum_values = [0,0]
    amount_sample_band = 0
    band_frequencies = calculate_band_frequencies(number_of_band_per_octave = 12)
    signal_frequencies = calibrated_mic_tf.freqs
    calibrated_mic_tf_values = calibrated_mic_tf.values
    uncalibrated_mic_tf_values = uncalibrated_mic_tf.values
    for index in progressBar(range(number_of_indexes), prefix = 'Writing data to csv file', suffix = '', decimals = 3, length = 100, fill = '█', printEnd = "\r"):
        freq = signal_frequencies[index]
        if not 20 < freq < 20000:
            continue
        else: 
            if freq > band_frequencies[index_band] and amount_sample_band != 0:
                average_calibrated_mic = sum_values[0] / amount_sample_band
                average_uncalibrated_mic = sum_values[1] / amount_sample_band
                writer.writerow([band_frequencies[index_band+1], average_calibrated_mic, average_uncalibrated_mic, 100 * abs(average_uncalibrated_mic - average_calibrated_mic) / average_uncalibrated_mic,sum_values[0] / sum_values[1]]) 
                index_band +=1
                sum_values = [0,0]
                amount_sample_band = 0

            values = [np.real(calibrated_mic_tf_values[index]), np.real(uncalibrated_mic_tf_values[index])]
            amount_sample_band += 1
            sum_values[0] += values[0]
            sum_values[1] += values[1]
    
# %%

print("Done!")