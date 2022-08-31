# Collection of utils to be used in the analysis

import numpy as np
import scipy as sp
from scipy import signal
import os
import sys
import librosa
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap

def compute_local_average(x, M_sec, Fs=1):

    L = len(x)
    M = int(np.ceil(M_sec * Fs))
    local_average = np.zeros(L)
    for m in range(L):
        a = max(m - M, 0)
        b = min(m + M + 1, L)
        local_average[m] = (1 / (2 * M + 1)) * np.sum(x[a:b])
        
    return local_average

def compute_novelty_spectrum(x, Fs=1, N=1024, H=256, gamma=100, M=10, norm=1, title="Spectral-Based Novelty"):
    
    X = librosa.stft(x, n_fft=N, hop_length=H, win_length=N, window='hanning')
    
    Y = np.log(1 + gamma*np.abs(X))
    
    Y_diff = np.diff(Y, axis=1)
    Y_diff[Y_diff < 0] = 0

    novelty = np.sum(Y_diff, axis=0)
    novelty = np.concatenate((novelty, np.array([0])))

    Fs_nov = Fs / H
    local_average = compute_local_average(x=novelty, M_sec=M, Fs=Fs_nov)
    novelty = novelty - local_average
    novelty[novelty < 0] = 0

    if(norm == 1):
        novelty = novelty / np.abs(max(novelty))
 
    feature_time_axis = np.arange(novelty.shape[0]) / Fs_nov
 
    plt.figure(figsize=(15,3))
    plt.plot(feature_time_axis,novelty)
    plt.title(title)
    peaks, properties = signal.find_peaks(novelty, prominence=0.05)
    peaks_sec = feature_time_axis[peaks]
    plt.scatter(peaks_sec, novelty[peaks], marker='o', color='blue' );

    return novelty

def compute_APM(x,lags=np.arange(20, 128)):  #lags depends on range of BPM we want to analize
    
    N = len(x)
    n_lags = len(lags)
    max_lag = lags[-1]

    #initialize autocorrelation phase matrix and counting matrix
    P = np.zeros((n_lags, max_lag))
    C = np.zeros((n_lags, max_lag))
    

    for lag_index in np.arange(n_lags):
        k = lags[lag_index]
        for phi in np.arange(k):
            n = np.ceil((N - phi)/k) # phi must be less then k
            i = np.array(phi + k*np.arange(n), dtype=int) # index in summation pf P(phi,k)
            P[lag_index, phi] = np.sum( x[i[:-1]] * x[i[1:]] ) # factor of moltiplication are shifted by 1
            C[lag_index, phi] = n-1 # how many elements we are summing
    
    C[C==0] = 1;

    return P, C

def influence(t, lags, N):
    
    n_lags = lags.shape[0]
    max_lag = lags[-1]

    I = np.zeros((n_lags, max_lag))

    for i in np.arange(n_lags):
        k = lags[i]  # period
        for phi in np.arange(k):
            # this is equal 1 if t is in the list, 0 otherwise
            I[i, phi] = t in [phi + i*k for i in np.arange(np.ceil(( N-phi)/k))]
    return I

def smooth(x, smooth_win_length=11, smooth_win_type='boxcar'):
    
    if x.ndim != 1:
        raise ValueError('smooth only accepts 1 dimension arrays.')

    if x.size < smooth_win_length:
        raise ValueError('Input vector needs to be bigger than window size.')

    if smooth_win_length<3:
        return x
    
    # mirror pad
    s = np.pad(x, int(smooth_win_length/2), mode='reflect')    
    # create window
    w = sp.signal.windows.get_window(smooth_win_type, smooth_win_length)
    # convolve with normalized window
    w_normalised = w / w.sum()
    y = np.convolve(s, w_normalised, mode='same')
    
    return y

def smooth_downsample_feature_sequence(X, Fs, filt_len=41, down_sampling=10, w_type='boxcar'):
    # use expand dims to add one dimesnion to the window, from (L, ) to (1,L) 
    filt_kernel = np.expand_dims(signal.get_window(w_type, filt_len), axis=0)
    X_smooth = signal.convolve(X, filt_kernel, mode='same') / filt_len
    X_smooth = X_smooth[:, ::down_sampling]
    Fs_feature = Fs / down_sampling
    return X_smooth, Fs_feature

def normalize_feature_sequence(X, norm='2', threshold=0.0001, v=None):
    K, N = X.shape
    X_norm = np.zeros((K, N))
    if norm == '1':
        if v is None:
            v = np.ones(K, dtype=np.float64) / K
        for n in range(N):
            s = np.sum(np.abs(X[:, n]))
            if s > threshold:
                X_norm[:, n] = X[:, n] / s
            else:
                X_norm[:, n] = v
    if norm == '2':
        if v is None:
            v = np.ones(K, dtype=np.float64) / np.sqrt(K)
        for n in range(N):
            s = np.sqrt(np.sum(X[:, n] ** 2))
            if s > threshold:
                X_norm[:, n] = X[:, n] / s
            else:
                X_norm[:, n] = v
    return X_norm

def compute_SM_dot(X,Y):
    S = np.dot(np.transpose(X), Y)
    return S

def compressed_gray_cmap(alpha=5, N=256):
    assert alpha != 0
    gray_values = np.log(1 + abs(alpha) * np.linspace(0, 1, N))
    gray_values /= gray_values.max()
    if alpha > 0:
        gray_values = 1 - gray_values
    else:
        gray_values = gray_values[::-1]
    gray_values_rgb = np.repeat(gray_values.reshape(256, 1), 3, axis=1)
    color_wb = LinearSegmentedColormap.from_list('color_wb', gray_values_rgb, N=N)
    return color_wb
