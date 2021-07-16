'''
Author : Louis Reine 
Date : 16/07/2021
Organization : ENSTA IMSIA
Small script used to calibrate a microphone using a comparison method.
The first microphone is considered as calibrated, and the second is considered to be calibrated.
We use farina's method to determine the transfer function of our microphone
Different methods will be used
Input 1 is the calibrated microhpone
Input 2 is the uncalibrated microphone
'''


import sys
import configparser
import measpy as mp
import csv
import os
import numpy as np
import time
from numpy.lib.function_base import average
from measpy.ni import ni_run_measurement, ni_get_devices
from measpy import audio
import matplotlib.pyplot as plt
plt.style.use('seaborn')

#Print interation progress
def progressBar(iterable, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
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

    def printProgressBar(iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                         (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


def run_calibration_measurement(out_signal_frequencies=[20, 20000], duration=3, amp_value=[1, 1], check_measurement=True):
    """
    Function launching measurement of a logsweep between out_signal_frequencies[0] and out_signal_frequencies[1]
    returning a Spectrum transfer function of the calibrated microphone and the uncalibrated microhpone.

    Args:
        out_signal_frequencies (list, optional): The range of the logsweep. Defaults to [20, 20000].
        duration (int, optional): The length of the logsweep
        amp_value (tuple(float,float), optional): The value of the amp used for the calibrated mic and uncalibrated mic in V/Pa. Defaults to [1, 1] 
        check_measurement (bool, optional): Choose to print the plot of measurement (signal and spectrum). Defaults to True.

    Returns:
        tuple(measpy.Spectrum, measpy.Spectrum) : tuple of calibrated and uncalibrated transfer function  
    """
    # First create a measurement
    # We send a logsweep signal to use Farina's method
    calibration_mesurement = mp.Measurement(out_sig="logsweep",
                                            fs=44100,
                                            in_map=[1, 2],
                                            out_map=[1],
                                            out_desc=['Out1'],
                                            out_dbfs=[1.0],
                                            in_desc=['Calibrated mic',
                                                     'Uncalibrated mic'],
                                            # Depends on the mic amp you are using. I use 316mV/Pa for amplifying the signal
                                            in_cal=amp_value,
                                            in_unit=['Pa', 'Pa'],
                                            in_dbfs=[1.0, 1.0],
                                            extrat=[0, 0],
                                            dur=duration,
                                            in_device='myDAQ1',
                                            out_device='myDAQ1',
                                            out_amp=1.0,
                                            io_sync=False,
                                            out_sig_freqs=out_signal_frequencies
                                            )

    print("Launching measurement...")
    ni_run_measurement(calibration_mesurement)
    print("Measurement done!")

    if check_measurement:
        calibration_mesurement.plot()
        plt.show()

    spectrum = calibration_mesurement.tfe()  # Convert to transfer function

    calibrated_mic_tf = spectrum["In1"]
    uncalibrated_mic_tf = spectrum['In2']

    if check_measurement:
        calibrated_mic_tf.plot()
        plt.show()

    return calibrated_mic_tf, uncalibrated_mic_tf


def write_data_to_csv(calibrated_mic_tf, uncalibrated_mic_tf, number_of_bands_per_octave):
    """
    Write the output csv file needed for calibration. Proceed by going through all the data band by band and averaging the values of all frequencies in the band. 

    Args:
        calibrated_mic_tf (measypy.Spectrum): [The calibrated microphone transfer function]
        uncalibrated_mic_tf ([measypy.Spectrum]): [The uncalibrated microphone transfer function]
        number_of_bands_per_octave ([int]): [Number of band to split the octave for easy data readability]
    """

    # To format the results we divide the spectrum into bands
    def calculate_band_frequencies(number_of_band_per_octave=3):
        """Function that creates the bound frequencies of frequency bands according to the number of bands you want. It starts by dividing the 1000Hz frequency by a factor based on the number of bands you want (2^(1/number_of_bands) until it reaches a frequency lower than 20Hz. Then it goes up again to get all frequencies".

        Args:
            number_of_band_per_octave (int, optional): [Number of octave]. Defaults to 3.

        Returns:
            [list]: [list of ascending ordered band frequencies]
        """
        factor = np.power(2, 1/number_of_band_per_octave)
        f_center = 1000
        while f_center > 20:
            f_center = f_center / factor
        frequencies = []
        while f_center < 20000:
            frequencies.append(int(np.round(f_center)))
            f_center = f_center * factor
        # Adding 20000Hz for convenience
        frequencies.append(20000)
        return frequencies

    print("Writing CSV Data...\n")

    # Generate the path of the CSV file
    csv_string_name = (time.ctime()).replace(":", "_").replace(" ", "_")
    csv_full_path = os.path.join(os.path.realpath(os.path.join(os.getcwd(
    ), os.path.dirname(__file__))), f'resultat_calibration_{csv_string_name}.csv')

    # Write to a csv file the different values
    # Create the header
    header = ['frequency (Hz)', 'value calibrated mic (dB)',
              'value uncalibrated mic (dB)', 'absolute variation (%)', 'gain factor (N/A)']

    # Add data to the csv
    with open(csv_full_path, "w", encoding='UTF8', newline='') as csv_output:
        writer = csv.writer(csv_output,  dialect='excel')
        writer.writerow(header)
        number_of_indexes = len(calibrated_mic_tf.freqs)
        print(f"Number of indexes : {number_of_indexes}")
        index_band = 0
        sum_values = [0, 0]
        amount_sample_band = 0
        band_frequencies = calculate_band_frequencies(
            number_of_bands_per_octave)
        signal_frequencies = calibrated_mic_tf.freqs
        calibrated_mic_tf_values = calibrated_mic_tf.values
        uncalibrated_mic_tf_values = uncalibrated_mic_tf.values
        for index in progressBar(range(number_of_indexes), prefix='Writing data to CSV file', suffix='', decimals=3, length=100, fill='▱', printEnd="\r"):
            freq = signal_frequencies[index]
            if not 20 < freq < 20000:
                continue
            else:
                if freq > band_frequencies[index_band] and amount_sample_band != 0:
                    average_calibrated_mic = sum_values[0] / amount_sample_band
                    average_uncalibrated_mic = sum_values[1] / \
                        amount_sample_band
                    writer.writerow([band_frequencies[index_band+1], average_calibrated_mic, average_uncalibrated_mic, 100 * abs(
                        average_uncalibrated_mic - average_calibrated_mic) / average_uncalibrated_mic, sum_values[0] / sum_values[1]])
                    index_band += 1
                    sum_values = [0, 0]
                    amount_sample_band = 0

                values = [np.real(calibrated_mic_tf_values[index]),
                          np.real(uncalibrated_mic_tf_values[index])]
                amount_sample_band += 1
                sum_values[0] += values[0]
                sum_values[1] += values[1]
    print("Done!")


if __name__ == "__main__":

    intro_string = "______  ______________ \r\n  /  _/  |/  / __/  _/ _ |\r\n _/ // /|_/ /\\ \\_/ // __ |\r\n/___/_/  /_/___/___/_/ |_|\r\n                          \r\n\r\n\r\n\r\n\r\nWelcome to the microphone calibration utility of IMSIA.\r\n This programm will create a CSV sheet with information to help calibrate a microphone by comparison. \r\nTo calibrate a microphone, please plug them to a Nexus Conditioning Amplifier, then plug the output of the Nexus to Input1 and Input2 of a MyDAQ NI card. \r\nAnalog Input 0 should be the calibrated microphone, Analog Input 1 should be the uncalibrated microphone.\r\nNext plug the speaker to the Analog Ouput 0 of the MyDAQ card (you can amplify it if necessary, be carefull what you do).\r\n"
    config = configparser.ConfigParser()
    print(intro_string)
    try:
        config.read(sys.argv[1])
        calibrated_mic_gain = config.getfloat('settings','calibrated_mic_gain')
        uncalibrated_mic_gain = config.getfloat('settings', 'uncalibrated_mic_gain')
        duration = config.getint('settings', 'duration')
        plot_data = config.getboolean('settings', 'plot_data')

    except:
        print("Configuration file not found, entering the values by hand\n")

        print("Enter the amplification factor of the Nexus Amplifier (float in V/Pa):")
        calibrated_mic_gain = float(
            input("Gain of the calibrated microphone : "))
        while not(isinstance(calibrated_mic_gain, float) and calibrated_mic_gain > 0.0):
            print("Please enter a valid input (float and positive)")
            calibrated_mic_gain = input("Gain of the calibrated microphone : ")

        uncalibrated_mic_gain = float(
            input("Gain of the uncalibrated microphone : "))
        while not(isinstance(uncalibrated_mic_gain, float) and uncalibrated_mic_gain > 0.0):
            print("Please enter a valid input (float and positive)")
            uncalibrated_mic_gain = input(
                "Gain of the uncalibrated microphone : ")

        duration = int(input("Duration of the logsweep : "))
        while not(isinstance(duration, int) and duration > 0):
            print("Please enter a valid input (int and positive)")
            duration = input("Duration of the logsweep : ")

        plot_answer = input("Do you want to see the data ? (y/n)\n")
        while plot_answer not in ["y", "n"]:
            print("Please enter a valid input (only y and n accepted")
            plot_answer = input("Do you want to see the data ? (y/n)\n")
        plot_data = (plot_answer == 'y')

    print("Now launching measurement procedure")

    calibrated_mic_tf, uncalibrated_mic_tf = run_calibration_measurement(out_signal_frequencies=[20, 20000], duration=duration, amp_value=[
        calibrated_mic_gain, uncalibrated_mic_gain], check_measurement=plot_data)

    csv_answer = input("Do you want to save in a CSV file the data ? (y/n)\n")
    while csv_answer not in ["y", "n"]:
        print("Please enter a valid input (only y and n accepted")
        csv_answer = input("Do you want to save in a CSV the data ? (y/n)\n")

    if csv_answer == "y":
        write_data_to_csv(calibrated_mic_tf, uncalibrated_mic_tf, 3)
    else:
        pass

    print("Done!")
