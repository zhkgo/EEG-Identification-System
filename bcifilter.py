# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 10:23:11 2020

@author: zhkgo
"""
from scipy import signal
from scipy.signal import butter
from scipy.signal import resample
from mne.filter import filter_data
from brainflow.data_filter import DataFilter, FilterTypes,DetrendOperations

class BciFilter:
    def __init__(self,low=1,high=40,sampleRate=1000,sampleRateTo=1000,idxs=[]):
        self.low=low
        self.high=high
        self.sampleRate=sampleRate
        self.sampleRateTo=sampleRateTo
        self.idxs=idxs
        # 8表示8阶
        nyq=self.sampleRate/2
        low=self.low/nyq
        high=self.high/nyq
        self.b,self.a=butter(4,[low,high],'bandpass')
        
    def deal(self,data):
        #先滤波后降采样
        if data.shape[1]<20:
            return data
        data=data[self.idxs]
        data=filter_data(data,self.sampleRate,self.low,self.high,verbose="ERROR")
        secs=data.shape[1]/self.sampleRate
        samps=int(secs*self.sampleRateTo)
        # print(data)
        if samps>0:
            data=resample(data,samps,axis=1)
        # self.ch_names
        return data

def filterForshow(data,sampleRate=250):
    for i in range(data.shape[0]):
        DataFilter.detrend(data[i], DetrendOperations.CONSTANT.value)
        DataFilter.perform_bandpass(data[i], sampleRate, 51.0, 100.0, 2,
                                FilterTypes.BUTTERWORTH.value, 0)
        DataFilter.perform_bandstop(data[i],sampleRate, 50.0, 4.0, 2,
                                FilterTypes.BUTTERWORTH.value, 0)
        DataFilter.perform_bandstop(data[i], sampleRate, 60.0, 4.0, 2,
                                FilterTypes.BUTTERWORTH.value, 0)
    return data