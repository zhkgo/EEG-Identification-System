# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 16:05:35 2021

@author: zhkgo
"""

"""
path为相对路径
timepoint为开始的秒数
sysTime 用unix时间戳表示
"""
import time
from collections import deque #线程安全
class VideoDeepLink(object):
    def __init__(self,ids=0,path="1.mp4",timePoint=0,sysTime=0):
        self.ids = ids
        self.path = path
        self.timePoint = timePoint
        self.sysTime = sysTime
    def toJson(self):
        dic={}
        for (name,value) in self.__dict__.items():
            if value!=None:
                dic[name]=value
        return dic
    def __str__(self):
        return "VideoDeepLink: id=%s,path=%s,timepoint=%s,sysTime=%s"%(self.ids,self.path,self.timePoint,self.sysTime)
class Linker:
    def __init__(self):
        self.cacheList=deque(maxlen=100) #若250ms加一次数据则250*100 缓存最多25秒数据
        self.deepLinks=[]
        self.batchsize=64 #采集到足够多的样本再推荐
    #ctime 表示脑电片段的起点时间
    def match(self,ctime,interval=0.25):
        clink=self.cacheList.popleft()
        while clink.sysTime<ctime:
            if ctime-clink.sysTime<interval:
                self.deepLinks.append(clink)
                if len(self.deepLinks)>=self.batchsize:
                    ff=self.deepLinks.copy()
                    self.deepLinks.clear()
                    return ff
                return 1
            else:
                clink=self.cacheList.popleft()
        self.cacheList.appendleft(clink)
        print("未匹配到合适视频帧")
        return 0
    def append(self,link):
        self.cacheList.append(link)