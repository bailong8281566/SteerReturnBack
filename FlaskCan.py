#-*-coding:utf-8-*-
from threading import Thread
import time,can,json,os
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
        print(carState)
        return json.dumps(carState)

    if request.method == 'POST':
        userReq['SteerReturnFlag'] = request.json['SteerReturnFlag']
        print(userReq)
        SteerReturnFlag = request.json['SteerReturnFlag']
        print('SteerReturnBack_Post:%d\n'%SteerReturnFlag)
        return json.dumps(userReq)


def rx_threading(bus):
    global EPS_STATE_LKA
    global CurSteerAngle
    global DriverOffFlag
    global HardwareState
    Driver_belt = 0
    main_state = 0
    door_state = 0
    gear_state = 0
    
    can_filters = \
        [{'can_id':0x495,'can_mask':0xfff,'extended':False},
        {'can_id':0x572,'can_mask':0xfff,'extended':False},
        {'can_id':0x432,'can_mask':0xfff,'extended':False},
        {'can_id':0x305,'can_mask':0xfff,'extended':False},
        {'can_id':0x349,'can_mask':0xfff,'extended':False},
        {'can_id':0x412,'can_mask':0xfff,'extended':False}]
    bus.set_filters(can_filters)
    
    while True:
        msg = bus.recv(1)
        if msg is not None:
            if msg.arbitration_id == 0x495:
                EPS_STATE_LKA = (msg.data[2] & 0x1c)>>2
            if msg.arbitration_id == 0x572:
                Driver_belt = (msg.data[0] & 0xc0)>>6
            if msg.arbitration_id == 0x432:
                main_state = (msg.data[6] & 0x03)
            if msg.arbitration_id == 0x412:
                door_state = (msg.data[6] & 0xf8)>>3
            if msg.arbitration_id == 0x349:
                gear_state = (msg.data[3] & 0xf)
            if msg.arbitration_id == 0x305:
                if ((msg.data[0] & 0x80)>>7) == 0:
                    CurSteerAngle = ((msg.data[0]<<8) +(msg.data[1]))*0.1
                else:
                    CurSteerAngle = -0.1*((~((msg.data[0]<<8) +(msg.data[1])) & 0xFFFF) + 1)
            #print(msg.arbitration_id,msg.data)
            # print('EPS_STATE_LKA%d'%EPS_STATE_LKA)
            #print('EPS_STATE_LKA%d'%EPS_STATE_LKA,'Driver_belt%d'%Driver_belt,'door_state%d'%door_state,
                 # 'main_state%d'%main_state,'CurSteerAngle%f'%CurSteerAngle)
            #if (Driver_belt == 1) and (main_state != 1) and (door_state == 0):
            if (Driver_belt == 1) and (door_state == 0):
                DriverOffFlag = 1
            else:
                DriverOffFlag = 0
                
            if gear_state == 0:
                HardwareState = 0
            else:
                HardwareState = 1
            
            #print('DriverOffFlag%d'%DriverOffFlag)

def tx_threading(bus):
    global EPS_STATE_LKA
    global CurSteerAngle
    global SteerReturnFlag,HardwareState
    global RB_FLAG,SteerReturnConfirm,EPS_Count
    data = bytearray([0,0,0,0,0,0,0,0])
    # print('SteerReturnFlag_global:%d\n'%SteerReturnFlag)
    while True:
        if SteerReturnFlag == 1:
            if EPS_STATE_LKA == 0:
                stEPSCtlCMD = 2
            elif EPS_STATE_LKA == 2:
                stEPSCtlCMD = 3
            elif EPS_STATE_LKA == 1:
                stEPSCtlCMD = 4
            
            elif EPS_STATE_LKA == 3:
                stEPSCtlCMD = 4
            else:
                stEPSCtlCMD = 2
                
            print('stEPSCtlCMD%d'%stEPSCtlCMD)
            if (CurSteerAngle > 0)  and (RB_FLAG == 0):
                RB_FLAG = 1
            if RB_FLAG == 1:
                if EPS_Count > 0:
                    setpoint = CurSteerAngle
                    EPS_Count = EPS_Count -1
                else:
                    setpoint = CurSteerAngle - 8
            if (RB_FLAG == 1) and (CurSteerAngle < -50):
                RB_FLAG = 2
            if RB_FLAG == 2:
                setpoint = CurSteerAngle + 8
            if(RB_FLAG == 2) and (CurSteerAngle > 0):
                setpoint = 0
                RB_FLAG = 0
                EPS_Count = 10
                SteerReturnConfirm = 1
            #     RB_FLAG = 3
            # if RB_FLAG == 3:
            #     setpoint = CurSteerAngle - 1
            # if(RB_FLAG ==3) and (CurSteerAngle < -2):
            #     setpoint = 0
            #     RB_FLAG = 0
            #     EPS_Count = 10
            #     SteerReturnConfirm = 1
                
            if (CurSteerAngle < 0)  and (RB_FLAG == 0):
                RB_FLAG = -1
            if RB_FLAG == -1:
                if EPS_Count > 0:
                    setpoint = CurSteerAngle
                    EPS_Count = EPS_Count -1
                else:
                    setpoint = CurSteerAngle + 8
            if (RB_FLAG == -1) and (CurSteerAngle > 50):
                RB_FLAG = -2
            if RB_FLAG == -2:
                setpoint = CurSteerAngle - 8
            if(RB_FLAG == -2) and (CurSteerAngle < 0):
                setpoint = 0
                RB_FLAG = 0
                EPS_Count = 10
                SteerReturnConfirm = 1
                
            #     RB_FLAG = -3
            # if RB_FLAG == -3:
            #     setpoint = CurSteerAngle + 1
            # if(RB_FLAG == -3) and (CurSteerAngle > 2):
            #     setpoint = 0
            #     RB_FLAG = 0
            #     EPS_Count = 10
            #     SteerReturnConfirm = 1
                
            # print('CurSteerAngle%.2f'%CurSteerAngle)
            # print('setpoint%d'%setpoint)
            if setpoint >= 0:
                byteAngle = (int(setpoint*10))<<2
            else:
                byteAngle = ((int(setpoint*10))& 0x3FFF)<<2
            byteAngle_H = (byteAngle & 0xff00)>>8
            byteAngle_L =  (byteAngle & 0xff)
            byteEPSCtlCMD = stEPSCtlCMD<<2
            cofficient = 0.5
            cofficientCMD = int((cofficient*100))<<1
            # data = bytearray([0x0,0x0,0x0,0x0,byteEPSCtlCMD,0xc9,byteAngle_H,byteAngle_L])
            data = bytearray([0x0,0x0,0x0,0x0,byteEPSCtlCMD,cofficientCMD,byteAngle_H,byteAngle_L])
        else:
            # stEPSCtlCMD = 2
            SteerReturnConfirm = 0
            RB_FLAG = 0
            EPS_Count = 10
            data = bytearray([0x0,0x0,0x0,0x0,0x8,0x0,0x0,0x0])
                
        print('RB_FLAG%d:'%RB_FLAG)
        print('EPS_Count%d:'%EPS_Count)
        print('EPS_STATE_LKA%d:'%EPS_STATE_LKA)
        print('SteerReturnFlag%d:\n'%SteerReturnFlag)
        # print('stEPSCtlCMD%d'%stEPSCtlCMD)
        msg = can.Message(is_extended_id=False, arbitration_id=0x3f2, data=data)
        try:
            bus.send(msg)
            time.sleep(0.0495)
        except:
            print('No buffer space available')
            HardwareState = 9
            time.sleep(10)


if __name__ == '__main__':
    sys = platform.system()
    if sys == "Windows":
        pass
    elif sys == "Linux":
        os.system('sudo ip link set can0 up type can bitrate 500000')
        bus = can.interface.Bus(bustype='socketcan',channel = 'can0',bitrate=500000)
        t1 = Thread(target=rx_threading, args=(bus,))
        t1.start()
        t2 = Thread(target=tx_threading,args=(bus,))
        t2.start()
    else:
        pass
    app.run(host='0.0.0.0',port='5000',debug=True,use_reloader=False)
