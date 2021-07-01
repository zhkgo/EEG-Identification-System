# -*- coding: utf-8 -*-
"""
Created on Tue Jun 29 14:20:14 2021

@author: zhkgo
"""

import socket
import pickle
from datatable import VideoDeepLink
d1=VideoDeepLink(ids=1,path='hello.mp4')
d2=VideoDeepLink(ids=2,path='hell2.mp4')
vs=[d1,d2]
server=socket.socket()
server.bind(('localhost',519))
server.listen(5)
while True:
    conn,addr=server.accept()
    try:
        data=conn.recv(40960)
        if len(data)==0:
            break
        conn.sendall(pickle.dumps(vs))
    except:
        print("链接断开")
    finally:
        conn.close()