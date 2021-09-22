from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
import numpy as np
import pickle
from sklearn import svm
from sklearn.pipeline import Pipeline
from pyriemann.estimation import XdawnCovariances
from pyriemann.tangentspace import TangentSpace
from sklearn.preprocessing import PowerTransformer

'''
demo 文件。
关键点两个函数，
1.getClassName 应当返回所有自定义类的类名，如果存在报错说不认识这个类的时候可以加入
2.getModel 返回模型对象，可以在里面加载模型参数等等，模型对象需要有predict函数，输入原始数据(batch,C,T)，输出(batch,1)
3.模型可以自己进行封装，比如把原来不是predict的封装成带predict函数的类，加入预处理等等。
'''
def getClassName():
    return ['BrainClass']

class BrainClass:
    def __init__(self,):
        with open("models/recognize.pkl","rb") as f:
            self.model=pickle.load(f)
        self.idxs=[i for i in range(15)]
        self.idxs.extend([18,19,21,22,23])
    def predict(self,x):
        x=x[:,self.idxs,:]
        return self.model.predict(x)
def getModel():
    return BrainClass()
