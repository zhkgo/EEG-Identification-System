"""
Created on Mon Jun 28 15:08:02 2021

@author: zhkgo
"""

from experiment import Experiment
from api.cytonParser import CytonDevice as BCI
# from api.dsiParse import DSIDevice as BCI
from api.reid import ReIDTCP
import configparser
from bcifilter import BciFilter,filterForshow
from datatable import VideoDeepLink,Linker
from flask import Flask,request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from threading import Lock
from myresponse import success,fail
import importlib
import traceback
import time
import numpy as np
thread_lock = Lock()
_thread=None

conf = configparser.ConfigParser()
experiment=None
reID=None
linker=Linker()
app = Flask(__name__,static_url_path="")
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = 'secret!'
CORS(app, supports_credentials=True)
socketio = SocketIO(app)


@app.route("/api/bcigo") 
def bcigo():
    try:
        bciReady()
    except Exception as e:
        return fail(str(e))
    # return success({"channels":experiment.channels})
    print(experiment.channels)
    return success({"channels":["Fp1", "Fp2", "C3", "C4", "P7", "P8", "O1", "O2"]})

@app.route('/api/getdata')
def getdata():
    global experiment
    # print("TCP END WHEN GET DATA",experiment.tcp.end)
    try:
        timeend=int(request.args.get('timeend'))
        arr,rend=experiment.getData(timeend,zerobegin=True)
        minnum,maxnum=None,None
        if rend>1000:
            arr2,rend2=experiment.getData(rend-1000,windows=1000,zerobegin=True)
            arr2=filterForshow(arr2,250)
            minnum=np.min(arr2,axis=1).reshape(-1,1)
            maxnum=np.max(arr2,axis=1).reshape(-1,1)
            arr=arr2[:,timeend-rend:]
            arr = (arr - minnum) / (maxnum - minnum)
        # arr=(arr-experiment.means)/experiment.sigmas
        # arr = (arr - np.max(arr,axis=1).reshape(-1,1)) / (np.max(arr,axis=1).reshape(-1,1)- np.min(arr,axis=1).reshape(-1,1))
        arr[np.isinf(arr)]=0
        # print(np.sum(arr<0))
    except Exception as e:
        print("ss")
        traceback.print_exc()
        return fail(str(e))
    #print("返回数据维度：", np.array(arr).shape)
    # print(np.array(arr).shape)
    # ['Fz','Cz','Pz','P3','P4','P7','P8','Oz','O1','O2','T7','T8']
    #选择部分通道显示
    # idxs=[0,6,3,2,4,10,11]
    # arr=arr[idxs]
    # print(np.array(arr).shape)
    return success({"data":arr.tolist(),'timeend':rend})
#开始记录数据
@app.route("/api/startRecord")
def startRecord():
    global experiment
    if experiment==None:
        return fail("请先创建实验")
    try:
        experiment.startRecord()
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success("开始记录当前脑纹数据")

#停止记录数据
@app.route("/api/stopRecord")
def stopRecord():
    global experiment
    if experiment==None:
        return fail("请先创建实验")
    try:
        name=request.args.get('subjectName')
        experiment.stopRecord(subjectName=name)
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success("当前脑纹采集成功")

@app.route("/api/startJudge")
def startJudge():
    global experiment
    subjects=["刘国文","章杭奎","潘泽宇","金宣妤"]
    res=None
    if experiment==None:
        return fail("请先创建实验")
    try:
        rr=[]
        for i in range(100):
            rr.append(experiment.predictOnce())
            print(subjects[rr[-1]],end=' ')
            time.sleep(0.05)
        # print("")
        res=subjects[max(rr,key=rr.count)] #小数据范围有效
    except Exception as e:
        traceback.print_exc()
        return success(subjects[0])
        return fail(str(e))
    return success(res)

@app.route("/api/reviseBaseline")
def reviseBaseline():
    global experiment
    try:
        experiment.reviseBaseline()
    except Exception as e:
        print(e)
        return fail(str(e))
    return success("修正基线成功")

@app.route("/api/closeBCI")
def closeBCI():
    global experiment
    experiment.finish(savefile=False)
    return success()


'''准备脑电接口'''
def bciReady(filename='config1.ini'):
    global experiment
    if experiment!=None:
        experiment.finish()
    conf.read(filename)
    experiment=Experiment()
    cur=conf['experiment']
    sessions=int(cur['session'])
    fitSessions=int(cur['fitsessions'])
    trials=int(cur['trials'])
    duration=int(cur['duration'])
    interval=int(cur['interval'])
    tmin=int(cur['tmin'])
    tmax=int(cur['tmax'])
    device=int(cur['device'])
    skipinterval=int(cur['skipinterval'])
    experiment.setParameters(sessions,fitSessions,trials,duration,interval,tmin,tmax,device,skipinterval)
    print("实验创建成功")
    
    cur=conf['filter']
    sampleRateFrom=int(cur['sampleRateFrom'])
    sampleRateTo=int(cur['sampleRateTo'])
    low=float(cur['low'])
    high=float(cur['high'])
    channels=cur['channels'].split(',')
    idxs=experiment.set_channel(channels)

    mfilter=BciFilter(low,high,sampleRateFrom,sampleRateTo,idxs)
    experiment.set_filter(mfilter)
    print("滤波-通道选择器初始化成功")
    
    module=importlib.import_module(conf['model']['path'])
    for name in module.getClassName():
        content="globals()['"+name+"']=module."+name
        exec(content)
    experiment.set_classfier(module.getModel())
    print("脑电判别模型准备成功")
    
    cur=conf['bcitcp']
    host=cur['host']
    port=int(cur['port'])
    tcpname=cur['name']
    tcp=BCI(host=host,port=port,name=tcpname)
    print("tcp: ",tcp)
    ch_nums=experiment.device_channels
    tcp.create_batch(ch_nums)
    experiment.set_dataIn(tcp)
    experiment.start_tcp()  #start To SaveData
    time.sleep(3)   #先接一部分数据
    print("脑电数据接入成功")
'''准备REID接口'''
# def reIDReady(filename='config.ini'):
#     global reID
#     conf.read(filename)
#     cur=conf['reidtcp']
#     reID=ReIDTCP(host=cur['host'],port=int(cur['port']))
if __name__=='__main__':    
    socketio.run(app, host='0.0.0.0',port=80, debug=False)
