import time
import communicate_lib
import serial

control_handle = communicate_lib.ControlHandle()
serial_instance = serial.Serial('COM3', 6000000)
control_handle.y_axis = 150
control_handle.z_axis = 100
while True:
    control_handle.y_axis = int(input('input y_axis:'))
    control_handle.z_axis = int(input('input z_axis:'))
    control_handle.pitch = int(input('input pitch:'))
    control_handle.send_position_control_command(serial_instance)
