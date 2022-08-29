# coding=UTF-8
import numpy as np
import math
from math import log, pow
import matplotlib.pyplot as plt
from tcp_server.tiaoshi06_01_RSSI_ranging_bluetooth_location import RSSI_location

if __name__ == "__main__":
    
    # 10个测试点真实坐标
    testpoints_xy = [ [0, 19.2], [0.8, 0.8], [0.8, 22.4], [1.6, 26.4], [1.6, 5.4], [2.4, 16], [2.4, 4], [2.4, 9.6], [3.2, 12], [3.2, 22.4] ]

    # 10个测试点信号强度
    testpoints_rssi_now = [
        {"11852":-89.03846153846153, "11854":-86.54347826086956, "11865":-82.20430107526882, "11866":-76.65656565656566, "11867":-72.84070796460178, "11868":-66.10526315789474, "11869":-84.73076923076923, "11870":-80.0},
        {"11851": -75.6923076923077, "11852":-79.88888888888889, "11853":-87.34782608695652, "11854":-80.78947368421052, "11865":-91.22727272727273, "11866":-90.875, "11867":-88.1891891891892, "11868":-89.88888888888889}, 
        {"11854":-86.6, "11865":-80.57291666666667, "11867":-70.6144578313253, "11868":-79.05, "11869":-69.13636363636364, "11870":-75.25688073394495},
        {"11854":-89.33333333333333, "11866":-89.82142857142857, "11867":-86.58823529411765, "11868":-80.10344827586206, "11869":-76.0, "11870":-74.93939393939394},
        {"11851": -77.4, "11852":-76.84848484848484, "11853":-75.25333333333333, "11854":-75.3157894736842, "11865":-78.7741935483871, "11866":-86.84210526315789, "11867":-86.93939393939394, "11868":-82.74242424242425, "11870":-90.0},
        {"11851": -88.04, "11852":-86.96363636363637, "11853":-81.19753086419753, "11854":-81.96296296296296, "11865":-68.76190476190476, "11866":-67.44565217391305, "11867":-70.88622754491018, "11868":-76.71126760563381, "11869":-83.66666666666667, "11870":-82.98058252427184},
        {"11851": -70.52380952380952, "11852":-70.48837209302326, "11853":-75.18604651162791, "11854":-82.4375, "11865":-78.38095238095238, "11866":-87.27586206896552, "11867":-88.0909090909091, "11868":-84.79411764705883, "11869":-88.28571428571429, "11870":-88.4},
        {"11851": -83.53333333333333, "11852":-76.95180722891567, "11853":-67.64583333333333, "11854":-74.56338028169014, "11865":-73.82051282051282, "11866":-81.32098765432099, "11867":-80.56923076923077, "11868":-86.22972972972973, "11869":-84.83720930232558, "11870":-88.33333333333333},
        {"11851": -87.71428571428571, "11852":-81.43055555555556, "11853":-75.72093023255815, "11854":-68.56701030927834, "11865":-78.20238095238095, "11866":-71.6082474226804, "11867":-78.26262626262626, "11868":-76.91428571428571, "11869":-87.33898305084746, "11870":-87.6268656716418},
        {"11854":-87.0, "11865":-79.29411764705883, "11866":-77.13513513513513, "11867":-76.59183673469387, "11868":-72.9795918367347, "11869":-79.175, "11870":-73.15384615384616}
    ]

    # 信标位置坐标
    signalxy = {"11851": [0.8+0.05, 2.4+0.12], "11852": [2.4-0.1, 4.8+0.2], "11853": [0.8-0.05, 7.2+0.12], "11854": [2.4, 9.6+0.12], "11865": [0.8-0.05, 12+0.12], "11866": [2.4, 14.4+0.12], "11867": [0.8-0.05, 16.8+0.12], "11868": [2.4, 19.2+0.12], "11869": [0.8-0.05, 21.6+0.12], "11870": [2.4, 24+0.05]}

    rssi_loc = RSSI_location(K=10, M=3, MAXD=31.21, MIND=2.4)
    for i in range(len(testpoints_rssi_now)):
        X = rssi_loc.loc(rssi=testpoints_rssi_now[i], signalxy=signalxy)
        print("测试点坐标X={}".format(X))


