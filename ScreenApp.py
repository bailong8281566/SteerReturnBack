# -*- coding: utf-8 -*-
"""
Created on Wed Jul 22 01:43:28 2020

@author: KumaSann
"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import WindowBase,Window
from kivy.properties import (
    NumericProperty, StringProperty, ObjectProperty,DictProperty,ListProperty
)
from kivy.core.audio import SoundLoader
import json

get_data = {'CurSteerAngle':0,'DriverOffFlag':0,'EPS_STATE_LKA':0,'HardwareState':0,'SteerReturnConfirm':0}
post_data = dict()
search_url = ''
EPS_STATE_LAST = 0
NetCounter = 0
ALARM = 0
Window.fullscreen = False
WindowBase.softinput_mode = 'below_target'

Builder.load_string("""
<MyLabelLEFT@Label>:
    font_name:'DroidSansFallback.ttf'
    size_hint_y: None
    height: 1.5 * self.texture_size[1]
    halign: 'right'
    font_size: '30sp'
<MyLabel@Label>:
    size_hint_y: None
    height: 1.5 * self.texture_size[1]
    font_size: '30sp'
         
<MyBox@BoxLayout>:
    canvas:
        Color:
            rgb: 255/255., 255/255., 255/255.
        Rectangle:
            pos: self.pos
            size: [self.size[i]-2 for i in range(2)]
<LoginPage>:
    FloatLayout:
        Image:
            source:'assets/background.jpg'
            allow_stretch:True
            keep_ratio:False
        TextInput:
            id: username
            hint_text: "TARGET IP"
            text:'192.168.1.103'
            foreground_color:[1,1,1,1]
            pos_hint: {'center_x': .5, 'center_y': 0.7}
            size_hint: .4, 0.08
            background_color:[0,0,0,0.3]
            multiline: False
            border:[20,20,20,20]
            on_text_validate: root.UserDefocus()
        Button:
            font_name:'DroidSansFallback.ttf'
            text: "登 录"
            pos_hint: {'center_x': .5, 'center_y': 0.55}
            size_hint: .4, 0.08
            background_color:[1,1,1,0.3]
            on_release: root.loginPage()

<PowerOnPage>:

                    
<Userpage>:
    canvas.after:
        Color:
            rgb: root.outline_rgb
        Line:
            width: 2.
            bezier:
                root.leftline_pos
        Color:
            rgb: root.outline_rgb
        Line:
            width: 2.
            bezier:
                root.rightline_pos

        Color:
            rgb: [1., 1., 1.]
        Line:
            dash_length: 10
            dash_offset: 5
            width: 1.
            bezier:
                root.leftline_pos
        Line:
            dash_length: 10
            dash_offset: 5
            width: 1.
            bezier:
                root.rightline_pos

    canvas:
        Color:
            rgb: 1, 1, 1
        Rectangle:
            source: 'assets/combine.png'
            size: self.size
    FloatLayout:
        id:floatlayout
        # Image:
        #     source:'assets/combine.png'
        #     allow_stretch:True
        #     keep_ratio:False
        BoxLayout:
            orientation: 'vertical'
            Label:
                size_hint: 1, .3
                font_name:'DroidSansFallback.ttf'
                font_size: '75sp'
                text: " [color=FFF0F5]方向盘转角显示[/color] "
                markup: True
            BoxLayout:
                orientation: 'horizontal'
                padding: 5
                spacing: 10
                Widget:
                    id:steerImage

                    size_hint: 0.5, .5
                    pos_hint:{'center_x':.5,'center_y':.6 }

                BoxLayout:
                    orientation: 'vertical'
                    BoxLayout:
                        
                        MyLabelLEFT:
                            text: "当前转角："
                        MyLabel:
                            id:curstAngle
                            text: str(root.CurSteerAngle) + '°'
                    BoxLayout:
                        MyLabelLEFT:
                            text: "网络状态："
                        MyLabel:
                            font_name:'DroidSansFallback.ttf'
                            text: root.NetState
                    BoxLayout:
                        MyLabelLEFT:          
                            text: "功能状态："
                        MyLabel:
                            font_name:'DroidSansFallback.ttf'
                            text: root.EPSState
                    Button:
                        id:userButton
                        pos_hint_x:.5
                        font_name:'DroidSansFallback.ttf'
                        text: root.buttonHint
                        font_size: '35sp'
                        size_hint: .8, .6
                        background_color:[1.,1.,1.,.3]
                        disabled:root.bottonState
                        color:[1.,1.,1.,1.]
                        opacity:root.visible
                        on_release: root.Straighten()
                    Widget

<Menu>:
    poweronpage:forpoweron
    userpage:foruser
    LoginPage:
        id:log
        name: "login_page"
    PowerOnPage:
        id:forpoweron
        name:'poweron_page'
    Userpage:
        id:foruser
        name: "user_page"
""")

class LoginPage(Screen):
    def loginPage(self):
        global search_url
        search_url = 'http://' + self.ids.username.text.strip() + ':5000'
        sound = SoundLoader.load('assets/beep1.wav')
        sound.play()
    def UserDefocus(self):
        self.loginPage()
class PowerOnPage(Screen):
    pass


class Userpage(Screen):
    SteerReturnFlag = NumericProperty(0)
    DriverOffFlag = NumericProperty(0)
    CurSteerAngle = NumericProperty(100)
    # CurrentSteerPic = StringProperty('assets/aeolus.png')
    NetState = StringProperty('网络初始化...')
    EPSState = StringProperty('回正功能状态初始化...')
    bottonState = NumericProperty(1)
    buttonHint = StringProperty('系统初始...')
    visible = NumericProperty(0)
    
    outline_rgb = ListProperty([0,0,0])
    leftline_pos = ListProperty()
    rightline_pos = ListProperty()
    DEBUG = 0

    blink_Flag = 0
    blink_timer = 0
    warn1_Flag = 0
    warn2_Flag = 0

    MAXtAngle = 90

    def Straighten(self):
        global search_url,ALARM
        headers = {'Content-type': 'application/json'}
        payload = {'SteerReturnFlag':1}
        req = UrlRequest(search_url, req_body=json.dumps(payload),req_headers=headers)
        sound = SoundLoader.load('assets/beep1.wav')
        sound.play()
        ALARM = 1
        print(payload)
    def line_pos_rgb(self):
        if self.DEBUG == 1:
            self.CurSteerAngle  = self.CurSteerAngle  - 1
            if self.CurSteerAngle < -100:
                self.DEBUG = -1
        if self.DEBUG == -1:
            self.CurSteerAngle  = self.CurSteerAngle  + 1
            if self.CurSteerAngle > 100:
                self.DEBUG = 1
        
        angle_ratio = (-1)*self.CurSteerAngle / self.MAXtAngle
        angle_ratio = 1 if angle_ratio > 1 else angle_ratio
        angle_ratio = -1 if angle_ratio < -1 else angle_ratio

        self.leftline_pos = [.12*self.width,.556*self.height, 
                ((angle_ratio*0.03)+0.12)*self.width,.75*self.height,
                ((angle_ratio*0.095)+0.12)*self.width,.825*self.height]
        
        self.rightline_pos = [.215*self.width,.556*self.height, 
                ((angle_ratio*0.03)+0.215)*self.width,.75*self.height,
                ((angle_ratio*0.095)+0.215)*self.width,.825*self.height]
        
        abs_angle_ratio = abs(angle_ratio)
        if abs_angle_ratio > 0.5:
            self.outline_rgb = [1.,2*(1-abs_angle_ratio),0.]
        else:
            self.outline_rgb = [2*abs_angle_ratio,1.,0.]
        
        
    def update(self):
        global get_data,search_url,EPS_STATE_LAST,ALARM
        
        self.CurSteerAngle = int(get_data['CurSteerAngle'])
        self.DriverOffFlag = get_data['DriverOffFlag']
        HardwareState = get_data['HardwareState']
        EPS_STATE_LKA = get_data['EPS_STATE_LKA']
        SteerReturnConfirm = get_data['SteerReturnConfirm']
        self.line_pos_rgb()
        
        if (SteerReturnConfirm == 1) or ((EPS_STATE_LAST == 3) and (EPS_STATE_LKA != 3)):
            headers = {'Content-type': 'application/json'}
            payload = {'SteerReturnFlag':0}
            req = UrlRequest(search_url, req_body=json.dumps(payload),req_headers=headers)
            if ALARM == 1:
                sound = SoundLoader.load('assets/beep2.wav')
                sound.play()
                ALARM = 0
        EPS_STATE_LAST = EPS_STATE_LKA
        self.buttonHint = '车辆已泊正'
        self.showPic()
        if (HardwareState == 0) and (SteerReturnConfirm != 1):
            #满足提醒条件（P档）且不是正在执行回正时，调用闪烁警示函数
            self.blink_warn()
        
        if (EPS_STATE_LKA == 4) or (self.NetState == 'CAN网络异常'):
            self.EPSState = '回正功能异常'
            self.buttonHint = '功能暂不可用'
            self.bottonState = 1
        elif EPS_STATE_LKA == 3:
            self.EPSState = '回正功能正常'
            self.buttonHint = '自动回正中...'
            self.bottonState = 1
        else:
            self.EPSState = '回正功能正常'
        if HardwareState == 0:
            #车熄火，显示按键
            self.NetState = '网络正常'
            # self.bottonState = 0
            self.visible = 1
        if HardwareState == 1:
            #车未熄火，不显示按键
            self.visible = 0
            self.NetState = '网络正常'
            self.bottonState = 1
        if HardwareState == 9:
            self.NetState = 'CAN网络异常'
            self.EPSState = '回正功能异常'
        if HardwareState == 10:
            self.NetState = '服务器异常'
            self.EPSState = '回正功能异常'
    def showPic(self):
        if (self.CurSteerAngle > 90):
            # self.CurrentSteerPic = 'assets/aeolus.png'
            self.buttonHint = '车辆未泊正，是否回正？'
            self.bottonState = 0
        if (self.CurSteerAngle < 90) and (self.CurSteerAngle > 45):
            # self.CurrentSteerPic = 'assets/aeolus.png'
            self.buttonHint = '车辆未泊正，请回正'
            self.bottonState = 1
        if (self.CurSteerAngle < 45) and (self.CurSteerAngle > -45):
            # self.CurrentSteerPic = 'assets/aeolus.png'
            self.buttonHint = '车辆已泊正'
            self.bottonState = 1
        if (self.CurSteerAngle < -45) and (self.CurSteerAngle > -90):
            # self.CurrentSteerPic = 'assets/aeolus.png'
            self.buttonHint = '车辆未泊正，请回正'
            self.bottonState = 1
        if (self.CurSteerAngle < -90) :
            # self.CurrentSteerPic = 'assets/aeolus.png'
            self.buttonHint = '车辆未泊正，是否回正？'
            self.bottonState = 0
    def blink_warn(self):
        '''
        P档
        ---方向盘转角绝对值大于45°时，图标闪烁
        ---方向盘转角绝对值大于45°小于180度时，提示bibi声
        ---方向盘转角绝对值大于180°时，提示didi声
        '''
        if abs(self.CurSteerAngle) >= 45:
            self.blink_timer = self.blink_timer + 1
            if self.blink_timer >= 2:
                self.ids.curstAngle.color[-1] = 1 - self.ids.curstAngle.color[-1]
                self.ids.userButton.color[-1] = 1 - self.ids.userButton.color[-1]
                self.blink_timer = 0
        else:
            self.ids.curstAngle.color[-1] = 1
            self.ids.userButton.color[-1] = 1
            
        if (abs(self.CurSteerAngle) >= 45) and (self.warn1_Flag == 0):
            self.warn1_Flag = 1
            sound = SoundLoader.load('assets/bibi.wav')
            sound.play()
        if abs(self.CurSteerAngle) < 45:
            self.warn1_Flag = 0

        if (abs(self.CurSteerAngle) >= 180) and (self.warn2_Flag == 0):
            self.warn2_Flag = 1
            sound = SoundLoader.load('assets/didi.wav')
            sound.play()
        if abs(self.CurSteerAngle) < 180:
            self.warn2_Flag = 0

        

class Menu(ScreenManager):
    poweronpage = ObjectProperty(None)
    userpage = ObjectProperty(None)
    data = DictProperty(None)
    # def __init__(self):
    #     self.transition = 'SlideTransition'
    def update(self, dt):
        global search_url
        # print('search_url:%s in menu\n'%search_url)
        self.request = UrlRequest(search_url, self.res,on_error=self.if_error,timeout=1)
        
        # self.poweronpage.update()
        self.userpage.update()
        
        
    def res(self,*args):
        global get_data,NetCounter
        NetCounter = 0
        print('IP  OK')
        try:
            tmp = json.loads(self.request.result)
            if tmp.keys() == get_data.keys():
                get_data = tmp
                
            else:
                get_data['HardwareState'] = 10
    
            self.current = "user_page"
        except:
            pass
        # if HardwareState == 2:
        #     self.current = "user_page"
        # else:
        #     self.current = "poweron_page"
        
    def if_error(self,request,result, *args):
        print('IP ERROR')
        global NetCounter
        NetCounter = NetCounter + 1
        if NetCounter > 5:
            self.current = "login_page"
            NetCounter = 0
    
class MyApp(App):
    def build(self):
        # Window.fullscreen = False
        # Window.size=(2560,1600)
        menu = Menu()
        Clock.schedule_interval(menu.update, 0.2)
        return menu

if __name__ == "__main__":
    MyApp().run()
