"""
Created on Mon Jun 28 15:08:02 2021

@author: zhkgo
"""

from experiment import Experiment
from api.dsiParse import DSIDevice as BCI
from api.reid import ReIDTCP
import configparser
from bcifilter import BciFilter
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


# def background_task():
#     global linker,experiment,reID
#     experiment.start()
#     while experiment.fitSessions>0:
#         socketio.sleep(0.1)
#         res=experiment.trainThreadStep1()
#         if res=="wait":
#             continue
#         if type(res) is str:
#             print(res)
#             socketio.emit('my_response',success({"finish":1,"message":res}))
#             break
#         socketio.emit('my_response',success({"finish":0,"sessions":res[0],"trials":res[1]}))
#     if experiment.fitSessions>0:
#         res=experiment.trainThreadStep2()
#         socketio.emit('my_response',success({"finish":1,"message":res}))
#     while True:
#         res=experiment.predictThread()
#         if res=="wait":
#             continue
#         if type(res) is str:
#             print(res)
#             socketio.emit('my_response',success({"finish":1,"message":res}))
#             break
#         res,ctime=res[0],res[2]
#         if res==1:
#             d=linker.match(ctime)
#             if type(d) is list:
#                 if reID is not None:
#                     d=reID.getMoreVideo(d)
#                 socketio.emit('newdeeplinks',success({"deeplinks":[item.toJson for item in d]}))
                
# @socketio.on('connect',namespace='/pushDeeplink')
# def recevDeepLink(jsondata):
#     print(type(jsondata))
#     print(jsondata)
#     model=VideoDeepLink
#     for (key,value) in jsondata.items():
#         model.__setattr__(key,value)
#     linker.append(model)
#     emit("receive",success({"finish":1,"message":"????????????"}))

# @socketio.on('startDetection')
# def startDetection():
#     global _thread
#     try:
#         if thread_lock:
#             _thread = socketio.start_background_task(target=background_task)
#     except Exception as e:
#         print(e)
#         emit("my_response",fail(str(e)))
#     emit("my_response",success())

@app.route("/api/bcigo") 
def bcigo():
    try:
        bciReady()
    except Exception as e:
        return fail(str(e))
    # return success({"channels":experiment.channels})
    print(experiment.channels)
    return success({"channels":['P3', 'P4', 'Fz', 'F3', 'F4', 'Fp1', 'Fp2']})

@app.route('/api/getdata')
def getdata():
    global experiment
    # print("TCP END WHEN GET DATA",experiment.tcp.end)
    try:
        timeend=int(request.args.get('timeend'))
        arr,rend=experiment.getData(timeend,zerobegin=True)
        arr=(arr-experiment.means)/experiment.sigmas
        # print(arr.tolist())
    except Exception as e:
        print("ss")
        traceback.print_exc()
        return fail(str(e))
    #print("?????????????????????", np.array(arr).shape)
    # print(np.array(arr).shape)
    # ['Fz','Cz','Pz','P3','P4','P7','P8','Oz','O1','O2','T7','T8']
    #????????????????????????
    idxs=[0,6,3,2,4,10,11]
    arr=arr[idxs]
    # print(np.array(arr).shape)
    return success({"data":arr.tolist(),'timeend':rend})
#??????????????????
@app.route("/api/startRecord")
def startRecord():
    global experiment
    if experiment==None:
        return fail("??????????????????")
    try:
        experiment.startRecord()
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success("??????????????????????????????")

#??????????????????
@app.route("/api/stopRecord")
def stopRecord():
    global experiment
    if experiment==None:
        return fail("??????????????????")
    try:
        name=request.args.get('subjectName')
        experiment.stopRecord(subjectName=name)
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success("????????????????????????")

@app.route("/api/startJudge")
def startJudge():
    global experiment
    subjects=["?????????","?????????","?????????","?????????"]
    res=None
    if experiment==None:
        return fail("??????????????????")
    try:
        rr=[]
        for i in range(100):
            rr.append(experiment.predictOnce())
            print(subjects[rr[-1]],end=' ')
            time.sleep(0.05)
        print("")
        res=subjects[max(rr,key=rr.count)] #?????????????????????
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
    return success("??????????????????")

@app.route("/api/closeBCI")
def closeBCI():
    global experiment
    experiment.finish(savefile=False)
    return success()


'''??????????????????'''
def bciReady(filename='config.ini'):
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
    print("??????????????????")
    
    cur=conf['filter']
    sampleRateFrom=int(cur['sampleRateFrom'])
    sampleRateTo=int(cur['sampleRateTo'])
    low=float(cur['low'])
    high=float(cur['high'])
    channels=cur['channels'].split(',')
    idxs=experiment.set_channel(channels)

    mfilter=BciFilter(low,high,sampleRateFrom,sampleRateTo,idxs)
    experiment.set_filter(mfilter)
    print("??????-??????????????????????????????")
    
    module=importlib.import_module(conf['model']['path'])
    for name in module.getClassName():
        content="globals()['"+name+"']=module."+name
        exec(content)
    experiment.set_classfier(module.getModel())
    print("??????????????????????????????")
    
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
    time.sleep(3)   #?????????????????????
    print("????????????????????????")
'''??????REID??????'''
# def reIDReady(filename='config.ini'):
#     global reID
#     conf.read(filename)
#     cur=conf['reidtcp']
#     reID=ReIDTCP(host=cur['host'],port=int(cur['port']))
if __name__=='__main__':    
    socketio.run(app, host='0.0.0.0',port=80, debug=False)
