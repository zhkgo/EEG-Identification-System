# -*- coding: utf-8 -*-
"""
Created on Tue Jun 29 13:29:39 2021

@author: zhkgo
"""
import threading
import socket
import pickle
from datatable import VideoDeepLink

class ReIDTCP():
    def __init__(self,host="localhost",port=519):
        self.tcp=socket.socket()
        self.tcp.connect((host,port))
    def getMoreVideo(self,deeplinks):
        print("待匹配视频列表")
        for item in deeplinks:
            print(item)
        data=pickle.dumps(deeplinks)
        self.tcp.sendall(data)
        data=self.tcp.recv(40960)
        deeplinks=pickle.loads(data)
        print("待呈现视频列表")
        for item in deeplinks:
            print(item)
        return deeplinks
    def close(self):
        self.tcp.close()