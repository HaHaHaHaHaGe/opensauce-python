from __future__ import division

import random
import numpy as np

from sys import platform

# Import user-defined global configuration variables
from conf.userconf import user_praat_path

from opensauce.praat import praat_pitch, praat_raw_pitch, praat_formants, praat_raw_formants

from opensauce.soundfile import SoundFile

from test.support import TestCase, wav_fns, get_sample_data, get_raw_data

# Shuffle wav filenames, to make sure testing doesn't depend on order
random.shuffle(wav_fns)

# Determine default path to Praat executable
if user_praat_path is not None:
    default_praat_path = user_praat_path
elif platform == 'darwin':
    default_praat_path = '/Applications/Praat.app/Contents/MacOS/Praat'
elif platform == 'win32' or platform == 'cygwin':
    default_praat_path = 'C:\Program Files\Praat\Praat.exe'
else:
    default_praat_path = '/usr/bin/praat'


class TestPraatPitch(TestCase):

    longMessage = True

    def test_pitch_against_voicesauce_data(self):
        # Test against Snack data generated by VoiceSauce
        # The data was generated on VoiceSauce v1.31 on Windows 7
        for fn in wav_fns:
            # Frame shift
            f_len = 1

            # Need ns (number of samples) and sampling rate (Fs) from wav file
            # to compute data length
            sound_file = SoundFile(fn)
            data_len = np.int_(np.floor(sound_file.ns / sound_file.fs / f_len * 1000))

            # Estimate F0 using Praat, use default VoiceSauce values
            F0_os = praat_pitch(fn, data_len, default_praat_path,
                                frame_shift=f_len, method='cc',
                                frame_precision=1, min_pitch=40, max_pitch=500,
                                silence_threshold=0.03, voice_threshold=0.45,
                                octave_cost=0.01, octave_jumpcost=0.35,
                                voiced_unvoiced_cost=0.14,
                                kill_octave_jumps=False, interpolate=False,
                                smooth=False, smooth_bandwidth=5)
            # Get VoiceSauce Praat F0 data
            F0_vs = get_raw_data(fn, 'pF0', 'strF0', 'FMTs', 'estimated')
            # Check that OpenSauce and VoiceSauce values are "close"
            self.assertTrue((np.isclose(F0_os, F0_vs, rtol=1e-05, atol=1e-08) | (np.isnan(F0_os) & np.isnan(F0_vs))).all())

    def test_pitch_raw(self):
        # Test against previously generated data to make sure nothing has
        # broken and that there are no cross platform or Praat version issues.
        # Data was generated by Praat v6.0.29 on Manjaro Linux.

        for fn in wav_fns:
            # Estimate raw Praat F0
            t_raw, F0_raw = praat_raw_pitch(fn, default_praat_path,
                                            frame_shift=1, method='cc',
                                            min_pitch=40, max_pitch=500,
                                            silence_threshold=0.03,
                                            voice_threshold=0.45,
                                            octave_cost=0.01,
                                            octave_jumpcost=0.35,
                                            voiced_unvoiced_cost=0.14,
                                            kill_octave_jumps=False,
                                            interpolate=False, smooth=False,
                                            smooth_bandwidth=5)
            # Get sample time data
            sample_data = get_sample_data(fn, 'praat', 'ptF0', '1ms')
            # Check number of entries is consistent
            self.assertEqual(len(t_raw), len(sample_data))
            # Check that computed time and sample_data are "close enough" for
            # floating precision
            self.assertTrue(np.allclose(t_raw, sample_data, rtol=1e-05, atol=1e-08))

            # Get sample F0 data
            sample_data = get_sample_data(fn, 'praat', 'pF0', '1ms')
            # Check number of entries is consistent
            self.assertEqual(len(F0_raw), len(sample_data))
            # Check that computed F0 and sample_data are "close enough" for
            # floating precision
            self.assertTrue((np.isclose(F0_raw, sample_data, rtol=1e-05, atol=1e-08) | (np.isnan(F0_raw) & np.isnan(sample_data))).all())

class TestPraatFormants(TestCase):

    longMessage = True

    # Names for expected measurements
    formants4_names = ['ptFormants', 'pF1', 'pF2', 'pF3', 'pF4',
                       'pB1', 'pB2', 'pB3', 'pB4']

    def test_formants_against_voicesauce_data(self):
        # Test against Snack data generated by VoiceSauce
        # The data was generated on VoiceSauce v1.31 on Windows 7
        for fn in wav_fns:
            # Frame shift
            f_len = 1
            # Need ns (number of samples) and sampling rate (Fs) from wav file
            # to compute data length
            sound_file = SoundFile(fn)
            data_len = np.int_(np.floor(sound_file.ns / sound_file.fs / f_len * 1000))
            # Estimate formants using Praat, use default VoiceSauce values
            formants_os = praat_formants(fn, data_len, default_praat_path,
                                         frame_shift=1, window_size=25,
                                         frame_precision=1, num_formants=4,
                                         max_formant_freq=6000)

            for k in self.formants4_names:
                if k != 'ptFormants':
                    # Get VoiceSauce Praat formant data
                    vs_data = get_raw_data(fn, k, 'strF0', 'FMTs', 'estimated')
                    # Check that OpenSauce and VoiceSauce values are "close"
                    self.assertTrue((np.isclose(formants_os[k], vs_data, rtol=1e-05, atol=1e-08) | (np.isnan(formants_os[k]) & np.isnan(vs_data))).all())

    def test_formants_raw(self):
        # Test against previously generated data to make sure nothing has
        # broken and that there are no cross platform or Praat version issues.
        # Data was generated by Praat v6.0.29 on Manjaro Linux.

        for fn in wav_fns:
            # Get raw Praat formant estimates
            estimates_raw = praat_raw_formants(fn, default_praat_path,
                                               frame_shift=1, window_size=25,
                                               num_formants=4,
                                               max_formant_freq=6000)

            for n in self.formants4_names:
                # Get sample data corresponding to key name
                sample_data = get_sample_data(fn, 'praat', n, '1ms')
                # Check number of entries is consistent
                self.assertEqual(len(estimates_raw[n]), len(sample_data))
                # Check that our estimates and sample_data are "close enough"
                # for floating precision
                self.assertTrue((np.isclose(estimates_raw[n], sample_data, rtol=1e-05, atol=1e-08) | (np.isnan(estimates_raw[n]) & np.isnan(sample_data))).all())
