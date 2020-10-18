#-*-coding:utf-8-*-
from threading import Thread
import time,json,os
from flask import Flask,request
import platform

# HardwareState  
# 0  CAR OFF
# 1  CAR ON
# 9  CAN BUS ERR
EPS_STATE_LKA = 0
CurSteerAngle = 0
SteerReturnFlag = 0
DriverOffFlag = 0
HardwareState = 0
RB_FLAG = 0
SteerReturnConfirm = 0
EPS_Count = 10

Count_Dir = 1

app = Flask(__name__)
carState = {'CurSteerAngle':0,'DriverOffFlag':0,'EPS_STATE_LKA':0,'HardwareState':0,'SteerReturnConfirm':0}
userReq = {'SteerReturnFlag':0}

@app.route('/',methods=['GET','POST'])
def car():
    global carState,userReq,DriverOffFlag,EPS_STATE_LKA,HardwareState,SteerReturnFlag,SteerReturnConfirm
    if request.method == 'GET':
        carState['CurSteerAngle'] = CurSteerAngle
        carState['DriverOffFlag'] = DriverOffFlag
        carState['EPS_STATE_LKA'] = EPS_STATE_LKA
        carState['HardwareState'] = HardwareState
        carState['SteerReturnConfirm'] = SteerReturnConfirm
        # print(carState['CurSteerAngle'])
        return json.dumps(carState)

    if request.method == 'POST':
        userReq['SteerReturnFlag'] = request.json['SteerReturnFlag']
        print(userReq)
        SteerReturnFlag = request.json['SteerReturnFlag']
        print('SteerReturnBack_Post:%d\n'%SteerReturnFlag)
        return json.dumps(userReq)

def rx_threading():
    global EPS_STATE_LKA
    global CurSteerAngle
    global DriverOffFlag
    global HardwareState
    global Count_Dir
    
    while True:
        if Count_Dir == 1:
            CurSteerAngle = CurSteerAngle + 1
            if CurSteerAngle > 200:
                Count_Dir = 0
        if Count_Dir == 0:
            CurSteerAngle = CurSteerAngle - 1
            if CurSteerAngle < -200:
                Count_Dir = 1
        # print(CurSteerAngle)
        time.sleep(0.05)

if __name__ == '__main__':
    t1 = Thread(target=rx_threading, args=())
    t1.start()
    app.run(host='0.0.0.0',port='5000',debug=True)