import pygame
import serial
import struct


class ControlHandle:

    def __init__(self):
        self.z_axis = 0
        self.y_axis = 0
        self.pitch = 0
        self.yaw_pos = 0
        self.yaw_neg = 0

    def get_joystick_signal(self, input_joystick: pygame.joystick.Joystick):
        if input_joystick is None:
            print("No joystick available!")
            return
        else:
            self.z_axis = int(input_joystick.get_axis(1) * 64)
            self.y_axis = int(input_joystick.get_axis(0) * 64)
            self.pitch = int(input_joystick.get_axis(3) * 64)
            self.yaw_pos = int((input_joystick.get_axis(5) + 1) * 128)
            self.yaw_neg = int((input_joystick.get_axis(4) + 1) * 128)
            return

    def send_speed_control_command(self, serial_instance: serial.Serial):
        if serial_instance is None:
            print("No serial port available!")
            return
        else:
            raw_data = [-23206, 0, self.z_axis, self.y_axis, self.pitch, self.yaw_pos, self.yaw_neg]

            data_to_send = b''
            for value in raw_data:
                data_to_send += struct.pack('>h', value)  # 'h'表示short类型，使用小端序

            serial_instance.write(data_to_send)
            return

    def send_position_control_command(self, serial_instance: serial.Serial):
        if serial_instance is None:
            print("No serial port available!")
            return
        else:
            raw_data = [-23206, 0, self.z_axis, self.y_axis, self.pitch, self.yaw_pos, self.yaw_neg]

            data_to_send = b''
            for value in raw_data:
                data_to_send += struct.pack('>h', value)  # 'h'表示short类型，使用小端序

            serial_instance.write(data_to_send)
            return


def send_play_music_command(serial_instance: serial.Serial):
    raw_data = [-23206, 14]
    data_to_send = b''
    for value in raw_data:
        data_to_send += struct.pack('>h', value)  # 'h'表示short类型，>表示使用大端序
    serial_instance.write(data_to_send)
    return


def send_debug_command(serial_instance: serial.Serial, acc: int, dec: int):
    raw_data = [-23206, 15, acc, dec, 0, 0, 0]
    data_to_send = b''
    for value in raw_data:
        data_to_send += struct.pack('>h', value)  # 'h'表示short类型，>表示使用大端序
    serial_instance.write(data_to_send)
    return
