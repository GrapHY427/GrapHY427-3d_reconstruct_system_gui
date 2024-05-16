import pygame
import serial
import struct

cdc_buffer_size = 64


class ControlHandle:

    def __init__(self):
        self.z_axis = 0
        self.y_axis = 0
        self.pitch = 0
        self.yaw_pos = 0
        self.yaw_neg = 0
        self.read_byte = None
        self.receive_data = []
        self.yaw_speed = 0
        self.yaw_angle = 0
        self.pitch_speed = 0
        self.pitch_angle = 0
        self.z_axis_position = 0
        self.y_axis_position = 0
        self.z_axis_speed = 0
        self.y_axis_speed = 0

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
            raw_data = [-23206, 1, self.z_axis, self.y_axis, self.pitch, self.yaw_pos]

            data_to_send = b''
            for value in raw_data:
                data_to_send += struct.pack('>h', value)  # 'h'表示short类型，使用小端序

            serial_instance.write(data_to_send)
            return

    def read_speed_control_report(self, serial_instance: serial.Serial, command: int):
        self.read_byte = serial_instance.read(cdc_buffer_size)
        self.receive_data = []
        for element in self.read_byte:
            self.receive_data.append(element)
        if len(self.receive_data) > 19:
            if self.receive_data[0] == 165 and self.receive_data[1] == 90 and self.receive_data[2] == 0:
                if self.receive_data[3] == command or self.receive_data[3] == 14:
                    self.yaw_angle = check_int16_overflow(self.receive_data[4] * 256 + self.receive_data[5])
                    self.y_axis_position = check_int16_overflow(self.receive_data[6] * 256 + self.receive_data[7])
                    self.z_axis_position = check_int16_overflow(self.receive_data[8] * 256 + self.receive_data[9])
                    self.pitch_angle = check_int16_overflow(self.receive_data[10] * 256 + self.receive_data[11])
                    self.yaw_speed = check_int16_overflow(self.receive_data[12] * 256 + self.receive_data[13])
                    self.y_axis_speed = check_int16_overflow(self.receive_data[14] * 256 + self.receive_data[15])
                    self.z_axis_speed = check_int16_overflow(self.receive_data[16] * 256 + self.receive_data[17])
                    self.pitch_speed = check_int16_overflow(self.receive_data[18] * 256 + self.receive_data[19])
        self.read_byte = None

    def zero_control_handle_data(self):
        self.z_axis = 0
        self.y_axis = 0
        self.pitch = 0
        self.yaw_pos = 0
        self.yaw_neg = 0
        self.yaw_speed = 0
        self.yaw_angle = 0
        self.pitch_speed = 0
        self.pitch_angle = 0
        self.z_axis_position = 0
        self.y_axis_position = 0
        self.z_axis_speed = 0
        self.y_axis_speed = 0


def send_zero_y_axis_command(serial_instance: serial.Serial):
    raw_data = [-23206, 2]
    data_to_send = b''
    for value in raw_data:
        data_to_send += struct.pack('>h', value)  # 'h'表示short类型，>表示使用大端序
    serial_instance.write(data_to_send)
    return


def send_zero_z_axis_command(serial_instance: serial.Serial):
    raw_data = [-23206, 3]
    data_to_send = b''
    for value in raw_data:
        data_to_send += struct.pack('>h', value)  # 'h'表示short类型，>表示使用大端序
    serial_instance.write(data_to_send)
    return


def send_zero_pitch_command(serial_instance: serial.Serial):
    raw_data = [-23206, 4]
    data_to_send = b''
    for value in raw_data:
        data_to_send += struct.pack('>h', value)  # 'h'表示short类型，>表示使用大端序
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


def check_int16_overflow(number):
    if number < 32768:
        return number
    else:
        return number - 65535
