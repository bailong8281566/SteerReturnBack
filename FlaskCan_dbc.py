#-*-coding:utf-8-*-
from threading import Thread
import time,can,json,os
from flask import Flask,request
import platform
import cantools

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


def rx_threading(bus,db):
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
                EPS_STATE_LKA = db.decode_message(msg.arbitration_id, msg.data)["State_of_EPS_for_LKA_function"]
            if msg.arbitration_id == 0x572:
                Driver_belt = db.decode_message(msg.arbitration_id, msg.data)["IC_seat_bealt_driver_state"]
            if msg.arbitration_id == 0x432:
                main_state = db.decode_message(msg.arbitration_id, msg.data)["GW_BCM_SEV_main_state"]
            if msg.arbitration_id == 0x412:
                door_state = db.decode_message(msg.arbitration_id, msg.data)["BCM_Opening_states"]
            if msg.arbitration_id == 0x349:
                gear_state = db.decode_message(msg.arbitration_id, msg.data)["TCU_Gear_lever_position"]
            if msg.arbitration_id == 0x305:
                CurSteerAngle = db.decode_message(msg.arbitration_id, msg.data)["Steering_wheel_angle"]

            if (Driver_belt == 1) and (door_state == 0):
                DriverOffFlag = 1
            else:
                DriverOffFlag = 0
                
            if gear_state == 0:
                HardwareState = 0
            else:
                HardwareState = 1

def tx_threading(bus,db):
    global EPS_STATE_LKA
    global CurSteerAngle
    global SteerReturnFlag,HardwareState
    global RB_FLAG,SteerReturnConfirm,EPS_Count

    msg_data_3F2 = {i.name:0 for i in db.get_message_by_name("ADAS_3F2_PSA1").signals}
    ADAS_3F2_PSA1_msg = db.get_message_by_name("ADAS_3F2_PSA1")
    # data = bytearray([0,0,0,0,0,0,0,0])
    # print('SteerReturnFlag_global:%d\n'%SteerReturnFlag)
    while True:
        t1 = time.time()
        # 每个循环周期，初始化msg_data的值为0
        ADAS_3F2_PSA1_data = msg_data_3F2
        
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

            cofficient = 0.6
            ADAS_3F2_PSA1_data["Column_angle_setpoint3F2"] = setpoint
            ADAS_3F2_PSA1_data["General_state_of_LKA_function3F2"] = stEPSCtlCMD
            ADAS_3F2_PSA1_data["Coefficient_toregulate_EPS"] = cofficient
        else:
            # stEPSCtlCMD = 2
            SteerReturnConfirm = 0
            RB_FLAG = 0
            EPS_Count = 10

        # print('stEPSCtlCMD%d'%stEPSCtlCMD)
        ADAS_3F2_PSA1_data = ADAS_3F2_PSA1_msg.encode(ADAS_3F2_PSA1_data)
        msg = can.Message(is_extended_id=False, arbitration_id=0x3f2, data=ADAS_3F2_PSA1_data)
        try:
            bus.send(msg)
            time.sleep(0.05 - (time.time()-t1))
        except:
            print('No buffer space available')
            HardwareState = 9
            time.sleep(10)


if __name__ == '__main__':
    sys = platform.system()
    CurDir = os.path.dirname(os.path.abspath(__file__))
    fileDir = os.path.join(CurDir,r"dbc/SteerCtl.dbc")
    db = cantools.database.load_file(fileDir)
    if sys == "Windows":
        pass
    elif sys == "Linux":
        os.system('sudo ip link set can0 up type can bitrate 500000')
        bus = can.interface.Bus(bustype='socketcan',channel = 'can0',bitrate=500000)
        t1 = Thread(target=rx_threading, args=(bus,db,))
        t1.start()
        t2 = Thread(target=tx_threading,args=(bus,db,))
        t2.start()
    else:
        pass
    app.run(host='0.0.0.0',port='5000',debug=True,use_reloader=False)
