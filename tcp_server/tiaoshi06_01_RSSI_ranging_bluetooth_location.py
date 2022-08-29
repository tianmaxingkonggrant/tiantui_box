# coding=UTF-8
import numpy as np
import math
from math import log, pow
import matplotlib.pyplot as plt
from typing import Optional

class RSSI_location:
    
    def __init__(self, K=10, M=3, MAXD=31.21, MIND=2.4):
        self.K = K
        self.M = M
        self.MAXD = MAXD
        self.MIND = MIND


    def RSSItoD(self, rssi):
        # RSSI = A - 10*n*lg(d), to get "A" and "n"
        # Input: [[d, rssi], ...], e.g. [[0.2, 87], ...], which 0.2表示距离0.2米，87表示信号强度87。
        # Output: {"A": value, "n": value}
        d = [i[0] for i in rssi]
        r = [i[1] for i in rssi]
        p = [-10*log(i, 10) for i in d]
        p_aver = math.fsum(p) / len(p)
        rssi_aver = math.fsum(r) / len(r)
        n = math.fsum([(p[i]-p_aver)*(r[i]-rssi_aver) for i in range(len(r))]
                    ) / math.fsum([math.pow(i-p_aver, 2) for i in p])
        A = rssi_aver - n * p_aver
        ret = {"A": A, "n": n}
        print("A={},N={}".format(A, n))
        # plt.plot(d, [A-10*n*log(di, 10) for di in d], color="green", marker="o")
        # plt.plot(d, r, "ro")
        # plt.show()

        return ret

    def position_err(self, pos_xy, tes_xy):
        # 功能：计算测试点的定位坐标和实际坐标之间的误差，包括单个误差、总体误差、误差最大值、误差最小值。
        # 输入：
        # pos_xy: [[10, 4], [2, 5], ...] 表示测试点的定位坐标
        # tes_xy: [[0, 19.2], [0.8, 0.8], ...]表示测试点的实际坐标
        # 输出:
        # {"every_err":[0.2, 0.3, ...], "whole_err":0.25, "max_err": 0.5, "min_err": 0.1}
        # print("pos_xy={}".format(pos_xy))
        pos_xy = [list(ele) for ele in pos_xy]
        tes_xy = [list(ele) for ele in tes_xy]
        print("In position_err, pos_xy ={}, tes_xy ={}".format(tes_xy, tes_xy))
        assert len(pos_xy) == len(tes_xy)
        # print("pos_xy={}".format(pos_xy))

        # 修改bug, del()删除列表元素后，列表后面的元素会依次向前移动，之后再删除元素，该元素的索引已经变化
        # for i in range(len(pos_xy)):
        #     if pos_xy[i] == -1:
        #         print("真实坐标{}处的采样信号，没有计算出定位坐标，错误原因可能是方程组出现奇异矩阵".format(tes_xy[i]))
        #         del(pos_xy[i])
        #         del(tes_xy[i])
        pos_xy = [ pos_xy[i] for i in range(len(pos_xy)) if pos_xy[i] != -1 ]
        tes_xy = [ tes_xy[i] for i in range(len(pos_xy)) if pos_xy[i] != -1 ]

        M = np.array(pos_xy)
        N = np.array(tes_xy)
        print("In position_err, M.shape={}, N.shape={}".format(M.shape, N.shape))
        T = np.power(M-N, 2)
        Ts = np.power(T.sum(axis=1), 0.5)
        # print("pos_xy={}, tes_xy={}, err={}".format(M, N, Ts))
        assert len(Ts) > 0
        for i in range(len(Ts)):
            print("真实坐标{}的采样信号，定位误差为{}".format(tes_xy[i], Ts[i]))
        print("总体误差，即平均误差，是{}".format(sum(Ts)/len(Ts)))
        print("最大误差是{}".format(max(Ts)))
        print("最小误差是{}".format(min(Ts)))
        # ret = {"every_err":list(Ts), "whole_err":0.25, "max_err": 0.5, "min_err": 0.1}
        return 


    def maxM(self, StoL_dxy, m):
        # 功能：取距离列表中最小的M个值，加入新矩阵；相应的返回对应的信标位置x矩阵、y矩阵
        # StoL_dxy: [ [float(d[i]), float(s_x[i]), float(s_y[i])] ]，其中元素已经按照d从小到大排列
        # m：M，即M
        # 返回：距离列表d, 信标位置x列表s_x, 信标位置y列表s_y
        d = [ StoL_dxy[i][0] for i in range(m) ]
        s_x = [ StoL_dxy[i][1] for i in range(m) ]
        s_y = [ StoL_dxy[i][2] for i in range(m) ]
        return d, s_x, s_y


    def AbW(self, s_x, s_y, d):
        # 功能：解算位置求解公式的参数矩阵A、b、W
        # 距离列表d, 信标位置x列表s_x, 信标位置y列表s_y
        # 返回：Array数组A、b、W
        print("In AbW, d={}, s_x={}, s_y={}".format(d, s_x, s_y))
        A = [ [s_x[i]-s_x[0], s_y[i]-s_y[0]] for i in range(1, len(d)) ]
        b = [ 0.5*(pow(s_x[i], 2) + pow(s_y[i], 2) - pow(s_x[0], 2) - pow(s_y[0], 2) - pow(d[i], 2) + pow(d[0], 2)) for i in range(1, len(d)) ]
        # 计算加权矩阵W
        w2 = [ pow(d[i]/d[0], 9) for i in range(1, len(d)) ]
        W = np.diag(w2)

        A = np.array(A)
        b = np.array(b)

        return A, b, W


    def weighted_ave(self, d, s_x, s_y):
        # 功能：测试点解算出距离各个信标的距离列表后，根据各个距离/距离之和的比值，从对应的信标坐标处加权平均计算出坐标
        # 距离列表d, 信标位置x列表s_x, 信标位置y列表s_y
        # 返回：[1.2, 2.0], 表示测试点坐标
        sum_d = sum(d)
        w_d = np.divide(d, sum_d)
        x = np.dot(w_d, s_x)
        y = np.dot(w_d, s_y)
        X = [x, y]
        return X


    def project2floor(self, d):
        # 功能：信标布设在屋顶，距离地面2.82m，蓝牙接收器放在椅子上，距离地面0.42m。把根据信号强度解算得到的蓝牙接收器和信标之间 的距离，投影到地面上
        # d: 距离列表d
        # 返回：修正后的距离列表edit_d
        D = np.array(d)
        D2 = np.power(D, 2)
        print("In project2floor, D={}, D2={}".format(D, D2))
        edit_d = list(np.power(D2 - pow(2.4, 2), 0.5))
        return edit_d


    def check_d(self, d):
        # 功能：加入距离限制，蓝牙接收器距离信标的距离，有最大值MAXD和最小值MIND限制
        # d: 距离列表d
        # 返回：距离列表中超出[最小值, 最大值]范围的元素的 索引列表
        err_di = [ i for i in range(len(d)) if d[i]>self.MAXD or d[i]<self.MIND ]
        return err_di


    def rssi_2_d(self, rssi, A, n):
        # 功能：将信号强度转换为距离
        # rssi: 信号强度，标量
        # A, n：无线信号-距离公式参数
        # 返回：信号强度反推的距离 
        d = math.pow(10, (A-rssi)/10.0/n)
        print("rssi={}, d={}".format(rssi, d))
        return d


    def coord_xy(self, A, W, b):
        # 功能：解算测试点坐标
        # A, b, W：解算方程组的参数矩阵，数据类型是np.array
        # 返回：np.array([3.2, 4.8])，表示测试点坐标
        X = np.matmul(np.linalg.inv(np.matmul(np.matmul(A.T, W), A)), np.matmul(np.matmul(A.T, np.linalg.inv(W)), b))
        return X


    def filter_err_di(self, d, s_x, s_y, err_di):
        # 功能：过滤掉d中的异常值（超过最大值MAXD，或小于最小值MIND）和s_x、s_y中对应位置的值
        # d: [1.6, 0.8, 3.2, ...] 表示距离列表
        # s_x: [0.4, 0.8, 2.4, ...] 表示信标的x坐标列表，和列表d一一对应
        # s_y：[1.6, 2.0, 3.2, ...] 表示信标的y坐标列表，和列表d一一对应
        # err_di: [0, 1, 2] 表示d中异常值的索引列表
        # 返回：过滤了异常值以后的列表d, s_x, s_y
        ori_len_d = len(d)
        d = [ d[i] for i in range(ori_len_d) if i not in err_di ]
        s_x = [ s_x[i] for i in range(ori_len_d) if i not in err_di ]
        s_y = [ s_y[i] for i in range(ori_len_d) if i not in err_di ]
        return d, s_x, s_y


    def struct_sort(self, d, s_x, s_y):
        # 功能：将列表d按照元素从小到大排列，列表s_x和s_y也按照相同顺序（和d中元素一一对应）排列
        # d: [1.6, 0.8, 3.2, ...] 表示距离列表
        # s_x: [0.4, 0.8, 2.4, ...] 表示信标的x坐标列表，和列表d一一对应
        # s_y：[1.6, 2.0, 3.2, ...] 表示信标的y坐标列表，和列表d一一对应
        # 返回：StoL_dxy: [ [float(d[i]), float(s_x[i]), float(s_y[i])] ]，其中元素已经按照d从小到大排列
        # 修正BUG：d[]中的元素都是浮点数，这里不应该把d[i]转换为整数，而应该转换为浮点数; 同样这里的s_x[]和s_y[]中的元素也都是浮点数，这里也不应该转换为整数，而应转换为浮点数
        dxy = np.array( [ [float(d[i]), float(s_x[i]), float(s_y[i])] for i in range(len(d)) ] )
        StoL_dxy = dxy[np.argsort(dxy[:, 0])]
        return StoL_dxy
 
    def loc(self, rssi, signalxy, paras={'A': -62.87264372051453, 'n': 1.7363625017299034}):
        # 修改：只取最大的M个信号强度计算
        # 修改：怀疑位置解算方法错误，修改A 和 b 的形式。检验无错，已完成
        # 修改：采用加权最小二乘法解算，误差大幅降低
        # Input:
        # rssi: {"851":-87, "852":-86, "853":-57, "854":-36}。表示当前测试点处的信号强度。最大情况下，有几个信标，就有几个信号强度。如果有的信标无信号，那么就没有对应的信号强度。
        # paras: {"A": A, "n": n}
        # signalxy: {"851": [0,3], "852":[8,3], "853":[16,3], "854":[24,3]}
        # Output: np.array([x, y])。表示当前位置的坐标。
        # print("signalxy={}".format(signalxy))
        pA = paras["A"]
        pn = paras["n"]
        d = [self.rssi_2_d(rssi[i], pA, pn) for i in rssi.keys()]
        s_xy = [signalxy[i] for i in signalxy.keys()]
        s_x = [i[0] for i in s_xy]
        s_y = [i[1] for i in s_xy]
        print("\n\nIn loc, originally, d={}, s_xy={}".format(d, s_xy))
        A, X, b = [], [], []

        if len(d) == 0:
            print("没有测得信号，当前位置坐标无解")
            return [-1]
        elif len(d) == 1:
            print("仅测得1个信号，当前位置坐标无解")
            return [-1]
        elif len(d) == self.K:
            print("完整获取{}个信号".format(self.K))
            
            # 排序后取信号强度前M位 对应的 距离和对应的信标坐标 
            assert rssi.keys() == signalxy.keys()
            StoL_dxy = self.struct_sort(d, s_x, s_y)

            d, s_x, s_y = self.maxM(StoL_dxy, self.M)
            err_di = self.check_d(d)
            print("In loc, len(d)=K, len(d)={}, err_di={}".format(len(d), err_di))

            d, s_x, s_y = self.filter_err_di(d, s_x, s_y, err_di)
            d = self.project2floor(d)
            print("In loc, len(d)=K, d={}".format(d))
            
            X = self.weighted_ave(d, s_x, s_y)
            print("当前位置坐标={}".format(X))
            return X
            # A, b, W = AbW(s_x, s_y, d)
            # try:
            #     X = coord_xy(A, W, b)
            #     print("当前位置坐标={}".format(X))
            #     return X
            # except:
            #     print("存在奇异矩阵，无解")
            #     return [-1]
        else:
            # 收集信号不到K个的位置坐标求解代码
            print("获取到{}个信号".format(len(d)))
            # retA = [i for i in listA if i in listB]
            join_tmp = [i for i in signalxy.keys() if i in rssi.keys()]
            d = [math.pow(10, (pA-rssi[i])/10.0/pn) for i in join_tmp]
            s_xy = [signalxy[i] for i in join_tmp]
            s_x = [i[0] for i in s_xy]
            s_y = [i[1] for i in s_xy]

            err_di = self.check_d(d)
            print("In loc, len(d)<K, len(d)={}, err_di={}".format(len(d), err_di))
            d, s_x, s_y = self.filter_err_di(d, s_x, s_y, err_di)
            d = self.project2floor(d)

            if len(d) == 0:
                print("根据信号反推得到的距离，没有值位于正常范围内，无解")
                return [-1]
            elif len(d) > self.M:
                StoL_dxy = self.struct_sort(d, s_x, s_y)
                d, s_x, s_y = self.maxM(StoL_dxy, self.M)
                print("In loc, len(d)<K, s_x={}, s_y={}, d={}".format(s_x, s_y, d))
                # 修正BUG： d已经在上面经过一次高差修正了，不需要再做一次高差修正，因此下面一行代码应当注释掉
                # d = project2floor(d)
            else:
                # 修正BUG：由于权重矩阵W的引入，W中元素是d[i]/d[0]，因此列表d[]中的元素必须要从小到大排序
                StoL_dxy = self.struct_sort(d, s_x, s_y)
                d, s_x, s_y = [ StoL_dxy[i][0] for i in range(len(StoL_dxy)) ], [ StoL_dxy[i][1] for i in range(len(StoL_dxy)) ], [ StoL_dxy[i][2] for i in range(len(StoL_dxy)) ]

            X = self.weighted_ave(d, s_x, s_y)
            print("当前位置坐标={}".format(X))
            return X



