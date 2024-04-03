import pygame
import pygame.locals as pygloc

import numpy as np
import serial
import struct
import time


class ControlHandle:

    def __init__(self, serial_instance: serial.Serial = None, control_joystick: pygame.joystick.Joystick = None):
        self.z_axis = 0
        self.y_axis = 0
        self.pitch = 0
        self.yaw_pos = 0
        self.yaw_neg = 0
        self.serial_instance = serial_instance
        self.control_joystick = control_joystick

    def update_control_data(self):
        if self.control_joystick is None:
            print("No joystick registered!")
            return
        else:
            self.z_axis = int(self.control_joystick.get_axis(1) * 64)
            self.y_axis = int(self.control_joystick.get_axis(0) * 64)
            self.pitch = int(self.control_joystick.get_axis(3) * 64)
            self.yaw_pos = int((self.control_joystick.get_axis(5) + 1) * 128)
            self.yaw_neg = int((self.control_joystick.get_axis(4) + 1) * 128)
            return

    def send_control_data(self):
        if self.serial_instance is None:
            print("No serial port available!")
            return
        else:
            raw_data = [-23206, 0, self.z_axis, self.y_axis, self.pitch, self.yaw_pos, self.yaw_neg]

            data_to_send = b''
            for value in raw_data:
                data_to_send += struct.pack('>h', value)  # 'h'表示short类型，使用小端序

            self.serial_instance.write(data_to_send)
            return


def send_debug_data(serial_instance: serial.Serial, acc: int, dec: int):
    raw_data = [-23206, 15, acc, dec, 0, 0, 0]
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


# 初始化pygame
pygame.init()

# 设置窗口大小
window_size = (960, 540)

# 创建窗口
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Joystick Monitor")

# 初始化游戏手柄
pygame.joystick.init()
joystick = None

# 检查是否有手柄连接
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
else:
    print("No joystick detected!")
    pygame.quit()
    exit()

# 设置字体用于显示文本
font = pygame.font.Font(None, 36)

# 游戏循环标志
running = True

# 应用变量
j = 0
camera_pitch = 0.0
camera_yaw = 0.0
y_axis = 0.0
camera_position = [0, 0, 1]  # Position of the camera in world coordinates
camera_rotation = [0, 0, 0]  # Rotation of the camera in Euler angles (roll, camera_pitch, camera_yaw)

# 初始化串口
usb_com = serial.Serial('COM3', 600000)
control_handle = ControlHandle(usb_com, joystick)

# 游戏循环
while running:
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygloc.QUIT:
            running = False

    # 填充背景
    screen.fill((10, 10, 10))

    # # 读取并显示每个轴的状态
    num_axes = joystick.get_numaxes()
    for i in range(num_axes):
        axis = joystick.get_axis(i)
        if i < 4:
            axis = int(axis * 64)
        else:
            axis = int((axis + 1) * 128)
        text = font.render(f"Axis {i}: {axis:d}", True, (255, 255, 255))
        # text = font.render(f"Axis {i}: {axis:.4f}", True, (255, 255, 255))
        screen.blit(text, (20, i * 30 + 20))

    # # 读取并显示每个按钮的状态
    num_buttons = joystick.get_numbuttons()
    for i in range(num_buttons):
        button = joystick.get_button(i)
        text = font.render(f"Button {i}: {button}", True, (255, 255, 255))
        screen.blit(text, (400, i * 30 + 20))

    # 发送控制数据到MCU
    if joystick.get_button(0) == 1:
        send_play_music_command(usb_com)
    else:
        control_handle.update_control_data()
        control_handle.send_control_data()

    # 刷新屏幕
    pygame.display.flip()

    # 控制更新速率
    pygame.time.Clock().tick(200)

# 退出pygame
pygame.quit()
usb_com.close()
