import argparse
from io import SEEK_CUR
import time
import numpy as np

import brainflow
import threading
from socket import *
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations


class CytonDevice:
    def __init__(self, serial_port="COM6", time_length=0.04, port="",host="",name="", sr=250, borad_id=0):
        # board_id: 选取pcb类型，0是8通cyton, 1是16通cyton
        self.params = BrainFlowInputParams()
        self.params.ip_port = 0
        self.params.serial_port = serial_port
        self.params.mac_address = ""
        self.params.other_info = ""
        self.params.serial_number = ""
        self.params.ip_address = "127.0.0.1"
        self.params.ip_protocol = 0  # 0: None
        self.params.timeout = 100
        self.params.file = "params.txt"

        self.end = 0
        self.name = name
        self.slice = int(time_length * sr)
        self.time_length = time_length
        self.chns = ["Fp1", "Fp2", "C3", "C4", "P7", "P8", "O1", "O2"]

        self.board = BoardShim(board_id=borad_id, input_params=self.params)

    def reinit(self):
        self.board.stop_stream()
        self.board.release_session()
        self.crate_batch()

    def create_batch(self,ch_names=["Fp1", "Fp2", "C3", "C4", "P7", "P8", "O1", "O2"], __=1):
        self.signals = np.zeros((len(ch_names), 3600000))
        # self.loads=np.load("data/lgw20211025105343.npy")[1:9]
        # print(self.loads)
        self.board.prepare_session()
        self.board.start_stream(1800 * 250, '')

    def parse_data(self):
        # while True:
        #     time.sleep(self.time_length)
        #     self.signals[:,self.end:self.end+6]=self.loads[:,self.end:self.end+6]
        #     self.end+=6
            # print(self.end)
        # 舍弃一段数据
        _ = self.board.get_board_data()
        while True:
            try:
                # 得到指定长度的数据片
                time.sleep(self.time_length)
                data = self.board.get_board_data()
                self.signals[:, self.end:self.end + data.shape[1]] = data[1:9,:]
                self.end += data.shape[1]
            except Exception as e:
                print(e)
                break


    def get_batch(self, startPos, maxlength=200):
        if startPos <= -1:
            startPos = self.end - maxlength
        rend = min(self.end, startPos + maxlength)
        arr = self.signals[:, startPos:rend]
        return arr, rend

    def saveData(self, name, startpos):
        ctime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        savepathvalue = "data/" + name + ctime + ".npy"
        np.save(savepathvalue, self.signals[:, startpos:self.end])

    def get_device_info(self):
        board_id = self.board.get_board_id()
        info = self.board.get_board_descr(board_id=board_id)
        return info["eeg_names"], info["sampling_rate"]

    def close(self, savefile=True):
        time.sleep(0.2)
        self.board.stop_stream()
        self.board.release_session()


# if __name__ == "__main__":
#     cyton = CytonDevice()
#     cyton.create_batch()
#     cyton.parse_data()

    # chns, sr, names = cyton.get_device_info()
    # print(chns, " ", sr, " ", names)
    # for i in range(10):
    #     data, span = cyton.get_batch()
    #     print(i)
    #     print(data.shape)
    #     print(span)