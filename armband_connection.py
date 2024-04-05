import argparse
import logging

import paho.mqtt.client as paho
from paho import mqtt
from paho.mqtt import client as mqtt_client
#import pygame
import time
import random
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

from mindrove.board_shim import BoardShim, MindRoveInputParams, BoardIds
from mindrove.data_filter import DataFilter, FilterTypes, DetrendOperations





class Graph:
    def __init__(self, board_shim):
        
        #self.joystick = joystick
        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 50
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate
        self.MAX_DATA_POINTS = 59
        
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title='Mindrove Plot',size=(800, 600))
        
        self.broker = '192.168.0.199'
        self.port = 1883
        self.topic = "ArmBand"
        self.client_id = f'python-mqtt-{random.randint(0, 1000)}'
        # username = 'emqx'
        # password = 'public'
        self.client = self.connect_mqtt()
        self.client.loop_start()
        
        

        self._init_timeseries()

        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(self.update_speed_ms)
        QtGui.QApplication.instance().exec_()
        
        

    def _init_timeseries(self):
        self.plots = list()
        self.curves = list()
        self.signals = [[], []]
        for i in range(len(self.exg_channels)):
            p = self.win.addPlot(row=i,col=0)
            p.showAxis('left', False)
            p.setMenuEnabled('left', False)
            p.showAxis('bottom', False)
            p.setMenuEnabled('bottom', False)
            if i == 0:
                p.setTitle('TimeSeries Plot')
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)

    def update(self):
        message = ""
        data = self.board_shim.get_current_board_data(self.num_points)
        

        for count, channel in enumerate(self.exg_channels):
            # plot timeseries
            DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 50.0, 4.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 60.0, 4.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            self.curves[count].setData(data[channel].tolist())

        #pygame.event.pump()
        #pygame.event.get()
        ##self.x_axis = self.joystick.get_axis(0)  # Left thumbstick horizontal (-1 to 1)
        #self.y_axis = self.joystick.get_axis(1)  # Left thumbstick vertical (-1 to 1)
        
        #self.signals[0].append(self.x_axis)
        #self.signals[1].append(self.y_axis)
        #self.curves[8].setData(self.signals[0])
        #self.curves[9].setData(self.signals[1])
        #print(len(self.signals[0]))
        #print(self.board_shim.MindRoveInputParams)
        for i in range(len(self.signals)):
            if len(self.signals[i]) > self.MAX_DATA_POINTS:
                self.signals[i].pop(0)
        message = " ".join(str(v) for v in data[3])
        print(message)
        self.app.processEvents()
        self.publish(self.client, message)
        
    
    def connect_mqtt(self):
        def on_connect(self, client, userdata, flags, rc):
        # For paho-mqtt 2.0.0, you need to add the properties parameter.
        # def on_connect(client, userdata, flags, rc, properties):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)
        # Set Connecting Client ID
        #self.client = mqtt_client.Client(self.client_id)

        # For paho-mqtt 2.0.0, you need to set callback_api_version.
        client = mqtt_client.Client(client_id=self.client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)

        # client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client
        
    def publish(self, client, message):
        msg_count = 1        
        #time.sleep(1)
        #msg = f"messages: {msg_count}"
        result = client.publish(self.topic, message)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{message}` to topic `{self.topic}`")
        else:
            print(f"Failed to send message to topic {self.topic}")
        msg_count += 1
        if msg_count > 5:
            msg_count = 0


def main():
    

    BoardShim.enable_dev_board_logger()
    logging.basicConfig(level=logging.DEBUG)


    params = MindRoveInputParams()
    
    

    try:
        
        board_shim = BoardShim(BoardIds.MINDROVE_WIFI_BOARD, params)
        board_shim.prepare_session()
        board_shim.start_stream()
        
        #pygame.init()
        #clock = pygame.time.Clock()
        #fps = 500
        #clock.tick(fps)
        #if not pygame.joystick.get_count():
       #     print("Error: No joystick detected.")
        #    quit()
        #joystick = pygame.joystick.Joystick(0)
        #joystick_name = joystick.get_name()
        #print(f"Connected joystick: {joystick_name}")
        #print("-----------------------------------------------------------------")
        
        Graph(board_shim)
        
    except BaseException:
        logging.warning('Exception', exc_info=True)
    finally:
        logging.info('End')
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()
            self.client.loop_stop()
            #pygame.quit()


if __name__ == '__main__':
    main()