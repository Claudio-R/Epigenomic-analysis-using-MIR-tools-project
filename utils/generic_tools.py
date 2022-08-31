# Collection of utils to be used in the analysis

import numpy as np
from scipy import signal
import os
import sys
import librosa
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap

def spectrogram(x, Fs, title):
    N, H = 512, 256

    # librosa has already implemented the stft
    X = librosa.stft(x, n_fft=N, hop_length=H, win_length=N, window='hanning')
    # log compression
    Y = np.log(1 + 10 * np.abs(X))
    
    time_axis = np.arange(X.shape[1]) / (Fs/H)
    frequency_axis = np.arange(X.shape[0]) / (N/Fs)
    
    x_ext = (time_axis[1] - time_axis[0])/2
    y_ext = (frequency_axis[1] - frequency_axis[0])/2
    image_extent = [time_axis[0]-x_ext, time_axis[-1]+x_ext, frequency_axis[0]-y_ext, frequency_axis[-1]-y_ext]
    
    plt.figure(figsize=(10,4))
    plt.imshow(Y, extent=image_extent, aspect='auto', origin='lower')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Frequency (Hz)')
    plt.title(title)

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
    """Computes similarty matrix from feature sequences using dot (inner) product
    """
    S = np.dot(np.transpose(Y),X)
    return S


def filter_diag_SM(S, L):
    """Path smoothing of similarity matrix by forward filtering along main diagonal

    Args:
        S: Similarity matrix (SM)
        L: Length of filter

    Returns:
        S_L: Smoothed SM
    """
    N = S.shape[0]
    M = S.shape[1]
    S_L = np.zeros((M,N))
    S_extend_L = np.zeros((N + L, M + L))
    S_extend_L[0:M,0:N] = S
    for pos in range(0,L):
        S_L = S_L + S_extend_L[pos:(M + pos), pos:(N + pos)]
    S_L = S_L/L
    return S_L

def compute_tempo_rel_set(tempo_rel_min, tempo_rel_max, num):
    """Compute logarithmically spaced relative tempo values

    Args:
        tempo_rel_min: Minimum relative tempo
        tempo_rel_max: Maximum relative tempo
        num: Number of relative tempo values (inlcuding the min and max)

    Returns:
        tempo_rel_set: Set of relative tempo values
    """
    tempo_rel_set = np.exp(np.linspace(np.log(tempo_rel_min), np.log(tempo_rel_max), num))
    return tempo_rel_set


def filter_diag_mult_SM(S, L=1, tempo_rel_set=[1], direction=0):
    """Path smoothing of similarity matrix by filtering in forward or backward direction
    along various directions around main diagonal
    Note: Directions are simulated by resampling one axis using relative tempo values
    Args:
        S: Self-similarity matrix (SSM)
        L: Length of filter
        tempo_rel_set: Set of relative tempo values
        direction: Direction of smoothing (0: forward; 1: backward)

    Returns:
        S_L_final: Smoothed SM
    """
    N = S.shape[0]
    M = S.shape[1]
    num = len(tempo_rel_set)
    S_L_final = np.zeros((M,N))

    for s in range(0, num):
        M_ceil = int(np.ceil(N/tempo_rel_set[s]))
        resample = np.multiply(np.divide(np.arange(1,M_ceil+1),M_ceil),N)
        np.around(resample, 0, resample)
        resample = resample -1
        index_resample = np.maximum(resample, np.zeros(len(resample))).astype(np.int64)
        S_resample = S[:,index_resample]

        S_L = np.zeros((M,M_ceil))
        S_extend_L = np.zeros((M + L, M_ceil + L))

        # Forward direction
        if direction==0:
            S_extend_L[0:M,0:M_ceil] = S_resample
            for pos in range(0,L):
                S_L = S_L + S_extend_L[pos:(M + pos), pos:(M_ceil + pos)]

        # Backward direction
        if direction==1:
            S_extend_L[L:(M+L),L:(M_ceil+L)] = S_resample
            for pos in range(0,L):
                S_L = S_L + S_extend_L[(L-pos):(M + L - pos), (L-pos):(M_ceil + L - pos)]

        S_L = S_L/L
        resample = np.multiply(np.divide(np.arange(1,N+1),N),M_ceil)
        np.around(resample, 0, resample)
        resample = resample-1
        index_resample = np.maximum(resample, np.zeros(len(resample))).astype(np.int64)

        S_resample_inv = S_L[:, index_resample]
        S_L_final = np.maximum(S_L_final, S_resample_inv)

    return S_L_final


def shift_cyc_matrix(X, shift=0):
    """Cyclic shift of features matrix along first dimension

    Args:
        X: Feature respresentation
        shift: Number of bins to be shifted

    Returns:
        X_cyc: Cyclically shifted feature matrix
    """
    #Note: X_cyc = np.roll(X, shift=shift, axis=0) does to work for jit
    K, N = X.shape
    shift = np.mod(shift, K)
    X_cyc = np.zeros((K,N))
    X_cyc[shift:K, :] = X[0:K-shift, :]
    X_cyc[0:shift, :] = X[K-shift:K, :]
    return X_cyc


def threshold_matrix(S, thresh, strategy='absolute', scale=False, penalty=0, binarize=False):
    """Treshold matrix in a relative fashion 

    Args:
        S: Input matrix
        thresh: Treshold (meaning depends on strategy)
        strategy: Thresholding strategy ('absolute', 'relative', 'local')
        scale: If scale=True, then scaling of positive values to range [0,1]
        penalty: Set values below treshold to value specified 
        binarize: Binarizes final matrix (positive: 1; otherwise: 0)
        Note: Binarization is applied last (overriding other settings)
        

    Returns:
        S_thresh: Thresholded matrix
    """
    if np.min(S)<0:
        raise Exception('All entries of the input matrix must be nonnegative')

    S_thresh = np.copy(S)
    N, M = S.shape
    num_cells = N*M
    
    if strategy == 'absolute':
        thresh_abs = thresh
        S_thresh[S_thresh < thresh] = 0
        
    if strategy == 'relative':
        thresh_rel = thresh
        num_cells_below_thresh = int(np.round(S_thresh.size*(1-thresh_rel)))
        if num_cells_below_thresh < num_cells:
            values_sorted = np.sort(S_thresh.flatten('F'))
            thresh_abs = values_sorted[num_cells_below_thresh]
            S_thresh[S_thresh < thresh_abs] = 0
        else:
            S_thresh = np.zeros([N,M])  
            
    if strategy == 'local':
        thresh_rel_row = thresh[0]
        thresh_rel_col = thresh[1]
        S_binary_row = np.zeros([N,M])   
        num_cells_row_below_thresh = int(np.round(M*(1-thresh_rel_row)))  
        for n in range(N):
            row = S[n,:]
            values_sorted = np.sort(row)
            if num_cells_row_below_thresh < M:
                thresh_abs = values_sorted[num_cells_row_below_thresh]
                S_binary_row[n,:] = (row>=thresh_abs)
        S_binary_col = np.zeros([N,M])
        num_cells_col_below_thresh = int(np.round(N*(1-thresh_rel_col)))  
        for m in range(M):
            col = S[:,m]
            values_sorted = np.sort(col)
            if num_cells_col_below_thresh < N:
                thresh_abs = values_sorted[num_cells_col_below_thresh]
                S_binary_col[:,m] = (col>=thresh_abs)
        S_thresh =  S * S_binary_row * S_binary_col
        
    if scale: 
        cell_val_zero = np.where(S_thresh==0)
        cell_val_pos = np.where(S_thresh>0)
        if len(cell_val_pos[0])==0:
            min_value = 0
        else:
            min_value = np.min(S_thresh[cell_val_pos])  
        max_value = np.max(S_thresh)
        #print('min_value = ', min_value, ', max_value = ', max_value)
        if max_value > min_value:
            S_thresh = np.divide((S_thresh - min_value) , (max_value -  min_value)) 
            if len(cell_val_zero[0])>0:
                S_thresh[cell_val_zero] = penalty   
        else:
            print('Condition max_value > min_value is voliated: output zero matrix')    
            
    if binarize:
        S_thresh[S_thresh > 0] = 1 
        S_thresh[S_thresh < 0] = 0
    return S_thresh



def compute_SM_dot(X,Y):
    S = np.dot(np.transpose(Y),X)    
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


def compute_SM_TI(X, Y, L=1, tempo_rel_set=[1], shift_set=[0], direction=2):
    """Compute enhanced similaity matrix by applying path smoothing and transpositions

    Args:
        X, Y: Input feature sequences
        L: Length of filter
        tempo_rel_set: Set of relative tempo values
        shift_set: Set of shift indices
        direction: Direction of smoothing (0: forward; 1: backward; 2: both directions)

    Returns:
        S_TI: Transposition-invariant SM
        I_TI: Transposition index matrix
    """
    for shift in shift_set:
        X_cyc = shift_cyc_matrix(X, shift)
        S_cyc = compute_SM_dot(X,X_cyc)

        if direction==0:
            S_cyc = filter_diag_mult_SM(S_cyc, L, tempo_rel_set, direction=0)
        if direction==1:
            S_cyc = filter_diag_mult_SM(S_cyc, L, tempo_rel_set, direction=1)
        if direction==2:
            S_forward = filter_diag_mult_SM(S_cyc, L, tempo_rel_set=tempo_rel_set, direction=0)
            S_backward = filter_diag_mult_SM(S_cyc, L, tempo_rel_set=tempo_rel_set, direction=1)
            S_cyc = np.maximum(S_forward, S_backward)
        if shift ==  shift_set[0]:
            S_TI = S_cyc
            I_TI = np.ones((S_cyc.shape[0],S_cyc.shape[1])) * shift
        else:
            #jit does not like the following lines
            #I_greater = np.greater(S_cyc, S_TI)
            #I_greater = (S_cyc>S_TI)
            I_TI[S_cyc>S_TI] = shift
            S_TI = np.maximum(S_cyc, S_TI)

    return S_TI, I_TI


def compute_SM_from_filename(fn_wav, L=21, H=5, L_smooth=16, tempo_rel_set=np.array([1]), shift_set=np.array([0]),
                           strategy = 'relative', scale=1, thresh= 0.15, penalty=0, binarize=0):
    """Compute an SSM

    Notebook: C4S2_SSM-Thresholding.ipynb

    Args:
        fn_wav: Path and filename of wav file
        L, H: Parameters for computing smoothed chroma features
        L_smooth, tempo_rel_set, shift_set: Parameters for computing SSM
        strategy, scale, thresh, penalty, binarize: Parameters used tresholding SSM

    Returns:
        x, x_duration: Audio signal and its duration (seconds)
        X, Fs_feature: Feature sequence and feature rate
        S_thresh, I: SSM and index matrix
    """
    # Waveform
    Fs = 22050
    x, Fs = librosa.load(fn_wav, Fs)
    x_duration = (x.shape[0])/Fs

    # Chroma Feature Sequence and SSM (10 Hz)
    C = librosa.feature.chroma_stft(y=x, sr=Fs, tuning=0, norm=2, hop_length=2205, n_fft=4410)
    Fs_C = Fs/2205

    # Chroma Feature Sequence and SSM
    X, Fs_feature = smooth_downsample_feature_sequence(C, Fs_C, filt_len=L, down_sampling=H)
    X = normalize_feature_sequence(X, norm='2', threshold=0.001)

    # Compute SSM
    S, I = compute_SM_TI(X, X, L=L_smooth, tempo_rel_set=tempo_rel_set, shift_set=shift_set, direction=2)
    S_thresh = threshold_matrix(S, thresh=thresh, strategy=strategy,
                                          scale=scale, penalty=penalty, binarize=binarize)
    return x, x_duration, X, Fs_feature, S_thresh, I
