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


#%%

#%%
# First create a measurement
# We send a logsweep signal to use Farina's method
# For the moment, we only run microphone measurement input, synchronised output will come later
calibration_mesurement = mp.Measurement(out_sig=None,
                    fs = 44100,
                    in_map=[1,2],
                    in_desc=['Calibrated mic','Uncalibrated mic'],
                    in_cal=[1.0,1.0],
                    in_unit=['Pa','Pa'],
                    in_dbfs=[1.0,1.0],
                    extrat=[0,0],
                    dur=10,
                    in_device='myDAQ1'
                    )

print("Launching measurement !")
ni_run_measurement(calibration_mesurement)

axes_calibration = calibration_mesurement.plot()
plt.show() #Check the data

calibrated_mic_signal = calibration_mesurement.data['In1'].fft().plot()
uncalibrated_mic_signal = calibration_mesurement.data['In2'].fft().plot()
calibrated_mic_signal = calibration_mesurement.data['In1'].plot()
(-calibration_mesurement.data['In1'] + calibration_mesurement.data['In2']).plot()

#comparison_axes = calibrated_mic_signal.tfe_farina(calibration_mesurement.out_sig_freqs).plot()
#uncalibrated_mic_signal.tfe_farina(calibration_mesurement.out_sig_freqs).plot(axes = comparison_axes)
plt.show()
# %%
