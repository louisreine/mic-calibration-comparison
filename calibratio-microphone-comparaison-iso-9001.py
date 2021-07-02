'''
Small script used to calibrate a microphone using a comparison method.
The first microphone is considered as calibrated, and the second is considered to be calibrated.
We use farina's method to determine the transfer function of our microphone
Different methods will be used
Input 1 is the calibrated microhpone
Input 2 is the uncalibrated microphone
'''

import measpy as mp
import matplotlib.pyplot as plt
from measpy.audio import audio_run_measurement, audio_get_devices
plt.style.use('seaborn')

indev = 'Built-in Microphone'
outdev = 'Built-in Output'

# First create a measurement
# We send a logsweep signal to use Farina's method

calibration_mesurement = mp.Measurement(out_sig='logsweep',
                    fs = 44100,
                    out_map=[1],
                    out_desc=['Out1'],
                    out_dbfs=[1.0],
                    in_map=[1,2],
                    in_desc=['Calibrated mic','Uncalibrated mic'],
                    in_cal=[1.0,1.0],
                    in_unit=['Pa','Pa'],
                    in_dbfs=[1.0,1.0],
                    extrat=[0,0],
                    out_sig_fades=[0,0],
                    dur=5,
                    in_device=indev,
                    out_device=outdev,
                    out_amp=1.0)

audio_run_measurement(calibration_mesurement)

axes_calibration = calibration_mesurement.plot()
plt.show() #Check the data

calibrated_mic_signal = calibration_mesurement.data['In1']
uncalibrated_mic_signal = calibration_mesurement.data['In2']

comparison_axes = calibrated_mic_signal.tfe_farina(calibration_mesurement.out_sig_freqs).plot()
uncalibrated_mic_signal.tfe_farina(calibration_mesurement.out_sig_freqs).plot(axes = comparison_axes)
plt.show()