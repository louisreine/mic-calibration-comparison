'''
Small script used to calibrate a microphone using a comparison method.
The first microphone is considered as calibrated, and the second is considered to be calibrated.
We use farina's method to determine the transfer function of our microphone
Different methods will be used
Input 1 is the calibrated microhpone
Input 2 is the uncalibrated microphone
'''
#%%
import measpy as mp
import matplotlib.pyplot as plt
from measpy import audio
from measpy.ni import ni_run_measurement, ni_get_devices
plt.style.use('seaborn')
import time

#%%

out_signal_frequencies = [20,20000]

#%%
# First create a measurement
# We send a logsweep signal to use Farina's method
# For the moment, we only run microphone measurement input, synchronised output will come later
calibration_mesurement = mp.Measurement(out_sig="logsweep",
                    fs = 44100,
                    in_map=[1,2],
                    out_map=[1],
                    out_desc=['Out1'],
                    out_dbfs=[1.0],
                    in_desc=['Calibrated mic','Uncalibrated mic'],
                    in_cal=[0.1,0.1], #Depends on the mic amp you are using. i use 100mV/Pa for amplifying the signal
                    in_unit=['Pa','Pa'],
                    in_dbfs=[1.0,1.0],
                    extrat=[0,0],
                    dur=10,
                    in_device='myDAQ1',
                    out_device='myDAQ1',
                    out_amp=1.0,
                    io_sync = False,
                    out_sig_freqs = out_signal_frequencies
                    )

print("Launching measurement !")
ni_run_measurement(calibration_mesurement)

axes_calibration = calibration_mesurement.plot()
plt.show() #Check the data

spectrum = calibration_mesurement.tfe() #Convert to transfer function



calibrated_mic_tf = spectrum["In1"].nth_oct_smooth(12, fmin = out_signal_frequencies[0], fmax = out_signal_frequencies[1])
uncalibrated_mic_tf = spectrum['In2'].nth_oct_smooth(12, fmin = out_signal_frequencies[0], fmax = out_signal_frequencies[1])

#%%

#Write to a file the different values 
with open(f"res_calibration{str(time.time())}.csv", "w") as f:
    for index in range(len(calibrated_mic_tf.freqs)):
        freq = calibrated_mic_tf.freqs[index]
        value_calibrated = calibrated_mic_tf.values[index]
        value_uncalibrated = uncalibrated_mic_tf.values[index]
        gain_calib_uncalib = value_calibrated / value_uncalibrated
        csv_string = f"{freq},{value_calibrated},{value_uncalibrated},{gain_calib_uncalib}\n"
        f.write(csv_string)
# %%
