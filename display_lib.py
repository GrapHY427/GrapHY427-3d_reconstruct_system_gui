import numpy as np
import pygame
import pygame.locals as pygloc
import serial.tools.list_ports

import communicate_lib
import matrix_lib

state_code = {'quit': -1, 'main_menu': 0, 'joystick_info_window': 1,
              'joystick_control_window': 2, 'auto_control_window': 3}

num_motor6020 = 1
num_motor2006 = 3

is_selecting_com_port = False
selected_index = -1
selected_port = None
baud_rate = 600000
time_out = 0.02

selected_joystick = 0
joystick = None

control_handle = None
serial_port = None

count = 0


# 主菜单, state码: 0
def render_main_menu(input_screen: pygame.surface.Surface, background: pygame.surface.Surface):
    global selected_joystick
    global joystick

    title_font = pygame.font.Font(None, 72)
    text_font = pygame.font.Font(None, 36)

    # 填充背景
    input_screen.fill((64, 64, 64))
    input_screen.blit(background, (0, 0))

    # #   渲染标题
    text = title_font.render(f"3D Reconstruction System", True, (255, 255, 255))
    input_screen.blit(text, (350, 40))

    # 创建一个表示按钮的矩形
    button1 = pygame.Rect(360, 200, 250, 80)
    button2 = pygame.Rect(720, 200, 250, 80)
    button3 = pygame.Rect(360, 400, 250, 80)
    button4 = pygame.Rect(720, 400, 250, 80)

    joystick_select_buttons = [pygame.Rect(50 + 300 * i, 600, 250, 80) for i in range(4)]

    # 设置按钮颜色
    button_color = (255, 255, 0)
    # 绘制圆角矩形按钮
    if joystick is None:
        if pygame.joystick.get_count() > 0:  # 尝试初始化手柄
            selected_joystick = 0
            joystick = pygame.joystick.Joystick(selected_joystick)
            joystick.init()
    if pygame.joystick.get_count() <= 0:
        pygame.draw.rect(input_screen, (128, 128, 128), button1, border_radius=10)  # 如果没有手柄连接，手柄相关按钮变灰
        text = text_font.render(f"Joystick Monitor", True, (0, 0, 0))
        input_screen.blit(text, (385, 230))

        pygame.draw.rect(input_screen, (128, 128, 128), button2, border_radius=10)
        text = text_font.render(f"Joystick Control", True, (0, 0, 0))
        input_screen.blit(text, (750, 230))

    else:
        pygame.draw.rect(input_screen, button_color, button1, border_radius=10)  # 如果有手柄连接，手柄相关按钮正常
        text = text_font.render(f"Joystick Monitor", True, (0, 0, 0))
        input_screen.blit(text, (385, 230))

        pygame.draw.rect(input_screen, button_color, button2, border_radius=10)
        text = text_font.render(f"Joystick Control", True, (0, 0, 0))
        input_screen.blit(text, (750, 230))

    pygame.draw.rect(input_screen, button_color, button3, border_radius=10)
    text = text_font.render(f"Automated Control", True, (0, 0, 0))
    input_screen.blit(text, (370, 430))

    pygame.draw.rect(input_screen, button_color, button4, border_radius=10)
    text = text_font.render(f"QUIT", True, (0, 0, 0))
    input_screen.blit(text, (810, 430))

    # 检查手柄连接情况并渲染
    text_font = pygame.font.Font(None, 32)

    text = text_font.render("Select a joystick, if no joystick connected, "
                            "some function will be disabled", True, (255, 255, 255))
    input_screen.blit(text, (250, 560))
    # 绘制手柄选择窗口
    for i, button_item in enumerate(joystick_select_buttons):
        pygame.draw.rect(input_screen, button_color, button_item)
        if i == selected_joystick and pygame.joystick.get_count() > 0:
            # 高亮选中手柄
            pygame.draw.rect(input_screen, (0, 255, 0), button_item)

    for i in range(4):
        if i == selected_joystick and pygame.joystick.get_count() > 0:
            # 更改显示文字
            text = text_font.render(f"Joystick {i} Selected", True, (0, 0, 0))
        elif i < pygame.joystick.get_count():
            text = text_font.render(f"Joystick {i} Available", True, (0, 0, 0))
        else:
            text = text_font.render(f"No Joystick", True, (0, 0, 0))
        input_screen.blit(text, (60 + 300 * i, 610))

    # 处理事件
    for event in pygame.event.get():
        if event.type == pygloc.QUIT:
            return state_code['quit'], joystick
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查鼠标是否在按钮1上
            if button1.collidepoint(event.pos):
                return state_code['joystick_info_window'], joystick
            # 检查鼠标是否在按钮2上
            if button2.collidepoint(event.pos):
                return state_code['joystick_control_window'], joystick
            # 检查鼠标是否在按钮3上
            if button3.collidepoint(event.pos):
                return state_code['auto_control_window'], joystick
            # 检查鼠标是否在按钮4上
            if button4.collidepoint(event.pos):
                return state_code['quit'], joystick
            for i, button in enumerate(joystick_select_buttons):
                if button.collidepoint(event.pos):
                    if i < pygame.joystick.get_count():
                        selected_joystick = i
                        joystick = pygame.joystick.Joystick(selected_joystick)
                        joystick.init()
    # 没有特殊事件，返回本窗口对应的state码
    return state_code['main_menu'], joystick


# 手柄信息监控窗口, state码: 1
def render_joystick_info_window(input_screen: pygame.surface.Surface, background: pygame.surface.Surface,
                                input_joystick: pygame.joystick.Joystick):
    title_font = pygame.font.Font(None, 60)
    text_font = pygame.font.Font(None, 48)

    # 填充背景
    input_screen.fill((64, 64, 64))
    input_screen.blit(background, (0, 0))

    # #   渲染标题
    text = title_font.render(f"Joystick Monitor", True, (255, 255, 255))
    input_screen.blit(text, (450, 40))

    # # # 读取并显示每个轴的状态
    num_axes = input_joystick.get_numaxes()
    for i in range(num_axes):
        axis = input_joystick.get_axis(i)
        if i < 4:
            axis = int(axis * 64)
        else:
            axis = int((axis + 1) * 128)
        text = text_font.render(f"Axis {i}: {axis:d}", True, (0, 255, 255))
        input_screen.blit(text, (200, i * 90 + 100))

    # # 读取并显示每个按钮的状态
    num_buttons = input_joystick.get_numbuttons()
    for i in range(num_buttons):
        button = input_joystick.get_button(i)
        if button == 0:
            text = text_font.render(f"Button {i}", True, (0, 255, 0))
        else:
            text = text_font.render(f"Button {i}", True, (255, 0, 0))
        input_screen.blit(text, (850, i * 36 + 100))

    # 创建一个表示按钮的矩形
    button = pygame.Rect(490, 590, 200, 80)

    # 设置按钮颜色
    button_color = (255, 255, 0)
    # 绘制圆角矩形按钮
    pygame.draw.rect(input_screen, button_color, button, border_radius=10)
    text_font = pygame.font.Font(None, 42)
    text = text_font.render(f"Main Menu", True, (0, 0, 0))
    input_screen.blit(text, (515, 615))

    for event in pygame.event.get():
        if event.type == pygloc.QUIT:
            return state_code['quit']
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查鼠标是否在按钮上
            if button.collidepoint(event.pos):
                return state_code['main_menu']
    # 没有特殊事件，返回本窗口对应的state码
    return state_code['joystick_info_window']


# 手柄控制窗口, state码: 2
def render_joystick_control_window(input_screen: pygame.surface.Surface, background: pygame.surface.Surface,
                                   input_joystick: pygame.joystick.Joystick):
    title_font = pygame.font.Font(None, 60)
    text_font = pygame.font.Font(None, 36)
    global selected_index
    global is_selecting_com_port
    global control_handle

    # 填充背景
    input_screen.fill((64, 64, 64))
    input_screen.blit(background, (0, 0))

    # 设置按钮颜色
    button_color = (255, 255, 0)

    listbox = None

    # 串口相关实例
    global selected_port
    global serial_port

    # #   渲染标题
    text = title_font.render(f"Joystick Control", True, (255, 255, 255))
    input_screen.blit(text, (450, 40))

    text = text_font.render(f"Joystick Monitor", True, (255, 255, 255))
    input_screen.blit(text, (60, 120))

    text = text_font.render(f"Motor Info", True, (255, 255, 255))
    input_screen.blit(text, (320, 120))

    # # # 读取并显示每个轴的状态
    num_axes = input_joystick.get_numaxes()
    for i in range(num_axes):
        axis = input_joystick.get_axis(i)
        if i < 4:
            axis = int(axis * 64)
        else:
            axis = int((axis + 1) * 128)
        text = text_font.render(f"Axis {i}: {axis:d}", True, (0, 255, 255))
        input_screen.blit(text, (100, i * 50 + 200))

        # 方便修改窗口位置相关参数
        width = 300
        height = 200
        step = 30
        text_color = (0, 255, 0)

        # # 读取并显示每个电机的状态
        if control_handle is not None:

            text = text_font.render(f"yaw speed: {control_handle.yaw_speed} rpm", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"pitch speed: {control_handle.pitch_speed} rpm", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"z_axis speed: {control_handle.z_axis_speed} rpm", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"y_axis speed: {control_handle.y_axis_speed} rpm", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"yaw angle: {int(control_handle.yaw_angle / 22.75)} degree", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"pitch angle: {int(control_handle.pitch_angle)} degree", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"z_axis position: {int(control_handle.z_axis_position)} mm", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"y_axis position: {int(control_handle.y_axis_position)} mm", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

        else:

            text = text_font.render(f"yaw speed: None", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"pitch speed: None", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"z_axis speed: None", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"y_axis speed: None", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"yaw angle: None", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"pitch angle: None", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"z_axis position: None", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

            text = text_font.render(f"y_axis position: None", True, text_color)
            input_screen.blit(text, (width, height))
            height += step

    # 创建一个表示按钮的矩形
    quit_button = pygame.Rect(490, 590, 200, 80)
    select_com_button = pygame.Rect(900, 200, 180, 40)

    # 绘制圆角矩形按钮
    pygame.draw.rect(input_screen, button_color, select_com_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Select COM Port", True, (0, 0, 0))
    input_screen.blit(text, (910, 210))

    pygame.draw.rect(input_screen, button_color, quit_button, border_radius=10)
    text_font = pygame.font.Font(None, 42)
    text = text_font.render(f"Main Menu", True, (0, 0, 0))
    input_screen.blit(text, (515, 616))

    # 初始化串口
    if selected_port is not None and serial_port is None:
        serial_port = serial.Serial(selected_port.name, baud_rate, timeout=time_out)
        control_handle = communicate_lib.ControlHandle()

    if selected_port is not None and serial_port is not None:
        if serial_port.name != selected_port.name:
            serial_port = serial.Serial(selected_port.name, baud_rate)

        if control_handle is not None:
            # 绘制状态指示文字
            text = text_font.render(selected_port.name + " work now", True, (255, 255, 255))
            input_screen.blit(text, (650, 500))

            text = text_font.render("Transform Matrix", True, (128, 0, 255))
            input_screen.blit(text, (650, 300))

            draw_matrix(input_screen,
                        matrix_lib.compute_camera_extrinsic_matrix(
                            [control_handle.y_axis_position / 1000 * np.sin(np.deg2rad(control_handle.yaw_angle)),
                             control_handle.y_axis_position / 1000 * np.cos(np.deg2rad(control_handle.yaw_angle)),
                             control_handle.z_axis_position / 1000],
                            [0, control_handle.pitch_angle, control_handle.yaw_angle]), (630, 330), (70, 35))

            # # 发送控制数据到MCU
            if input_joystick.get_button(0) == 1:
                communicate_lib.send_play_music_command(serial_port)
            else:
                control_handle.get_joystick_signal(input_joystick)

                control_handle.send_speed_control_command(serial_port)

                control_handle.read_speed_control_report(serial_port, 0)

    # 串口选择界面
    if is_selecting_com_port:
        ports_list = list(serial.tools.list_ports.comports())

        # 设置listbox颜色
        listbox_color = (128, 128, 128)

        text_font = pygame.font.Font(None, 32)
        default_listbox = [pygame.Rect(650, 200, 250, 30)]

        if len(ports_list) <= 0:
            # 绘制listbox
            for i, listbox_item in enumerate(default_listbox):
                pygame.draw.rect(input_screen, listbox_color, listbox_item)

            text = text_font.render("No serial device!", True, (255, 255, 255))
            input_screen.blit(text, (650, 210))
        else:
            # 创建一个表示listbox的列表
            listbox = [pygame.Rect(650, 230 + 30 * i, 250, 30) for i in range(len(ports_list))]

            # 绘制listbox
            for i, listbox_item in enumerate(default_listbox):
                pygame.draw.rect(input_screen, listbox_color, listbox_item)

            for i, listbox_item in enumerate(listbox):
                pygame.draw.rect(input_screen, listbox_color, listbox_item)
                if i == selected_index:
                    # 高亮选中串口
                    pygame.draw.rect(input_screen, (0, 0, 250), listbox_item)

            text = text_font.render("Available serial device:", True, (255, 255, 255))
            input_screen.blit(text, (650, 210))

            for i, comport in enumerate(ports_list):
                text = text_font.render(comport.device, True, (255, 255, 255))
                input_screen.blit(text, (650, 240 + 30 * i))
                if i == selected_index:
                    selected_port = comport

                    pygame.draw.rect(input_screen, listbox_color, default_listbox[0])
                    text = text_font.render(comport.device, True, (255, 255, 255))
                    input_screen.blit(text, (650, 210))

    for event in pygame.event.get():
        if event.type == pygloc.QUIT:
            return -1
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查鼠标是否在按钮上
            if quit_button.collidepoint(event.pos):
                return 0
            if select_com_button.collidepoint(event.pos):
                is_selecting_com_port = not is_selecting_com_port
                return 2
            if is_selecting_com_port:
                # 检查鼠标是否在某个listbox上
                if listbox is not None:
                    for i, listbox_item in enumerate(listbox):
                        if listbox_item.collidepoint(event.pos):
                            if selected_index != i:
                                selected_index = i
                            else:
                                selected_index = -1
                                if serial_port is not None:
                                    serial_port.close()
                                    serial_port = None
                                    selected_port = None
                                    control_handle = None

    # 没有特殊事件，返回本窗口对应的state码
    return state_code['joystick_control_window']


# 自动控制窗口, state码: 3
def render_auto_control_window(input_screen: pygame.surface.Surface, background: pygame.surface.Surface):
    title_font = pygame.font.Font(None, 60)
    global selected_index
    global is_selecting_com_port
    global control_handle

    # 串口相关实例
    global selected_port
    global serial_port

    # 填充背景
    input_screen.fill((64, 64, 64))
    input_screen.blit(background, (0, 0))

    # 设置按钮颜色
    button_color = (255, 255, 0)

    listbox = None

    # #   渲染标题
    text = title_font.render(f"Automated Control", True, (255, 255, 255))
    input_screen.blit(text, (450, 40))

    # 创建一个表示按钮的矩形
    quit_button = pygame.Rect(490, 590, 200, 80)
    select_com_button = pygame.Rect(900, 200, 180, 40)

    # 绘制圆角矩形按钮
    pygame.draw.rect(input_screen, button_color, select_com_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Select COM Port", True, (0, 0, 0))
    input_screen.blit(text, (910, 210))

    pygame.draw.rect(input_screen, button_color, quit_button, border_radius=10)
    text_font = pygame.font.Font(None, 42)
    text = text_font.render(f"Main Menu", True, (0, 0, 0))
    input_screen.blit(text, (515, 616))

    # 方便修改窗口位置相关参数
    width = 100
    height = 150
    step = 35

    # # 读取并显示每个电机的状态
    if control_handle is not None:

        text = text_font.render(f"yaw speed: {control_handle.yaw_speed} rpm", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"pitch speed: {control_handle.pitch_speed} rpm", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"z_axis speed: {control_handle.z_axis_speed} rpm", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"y_axis speed: {control_handle.y_axis_speed} rpm", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"yaw angle: {int(control_handle.yaw_angle / 22.75)} degree", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"pitch angle: {int(control_handle.pitch_angle)} degree", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"z_axis position: {int(control_handle.z_axis_position)} mm", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"y_axis position: {int(control_handle.y_axis_position)} mm", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

    else:

        text = text_font.render(f"yaw speed: None", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"pitch speed: None", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"z_axis speed: None", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"y_axis speed: None", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"yaw angle: None", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"pitch angle: None", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"z_axis position: None", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"y_axis position: None", True, (0, 255, 0))
        input_screen.blit(text, (width, height))
        height += step

    # 初始化串口
    if selected_port is not None and serial_port is None:
        serial_port = serial.Serial(selected_port.name, baud_rate)
        control_handle = communicate_lib.ControlHandle()

    if selected_port is not None and serial_port is not None:
        if serial_port.name != selected_port.name:
            serial_port = serial.Serial(selected_port.name, baud_rate)

        if control_handle is not None:
            # 绘制状态指示文字
            text = text_font.render(selected_port.name + " work now", True, (255, 255, 255))
            input_screen.blit(text, (650, 500))

            text = text_font.render("Transform Matrix", True, (128, 0, 255))
            input_screen.blit(text, (650, 300))

            draw_matrix(input_screen,
                        matrix_lib.compute_camera_extrinsic_matrix(
                            [control_handle.y_axis_position / 1000 * np.sin(np.deg2rad(control_handle.yaw_angle)),
                             control_handle.y_axis_position / 1000 * np.cos(np.deg2rad(control_handle.yaw_angle)),
                             control_handle.z_axis_position / 1000],
                            [0, control_handle.pitch_angle, control_handle.yaw_angle]), (630, 330), (70, 35))

            # # 发送控制数据到MCU
            control_handle.send_speed_control_command(serial_port)

    # 串口选择界面
    if is_selecting_com_port:
        ports_list = list(serial.tools.list_ports.comports())

        # 设置listbox颜色
        listbox_color = (128, 128, 128)

        text_font = pygame.font.Font(None, 32)
        default_listbox = [pygame.Rect(650, 200, 250, 30)]

        if len(ports_list) <= 0:
            # 绘制listbox
            for i, listbox_item in enumerate(default_listbox):
                pygame.draw.rect(input_screen, listbox_color, listbox_item)

            text = text_font.render("No serial device!", True, (255, 255, 255))
            input_screen.blit(text, (650, 210))
        else:
            # 创建一个表示listbox的列表
            listbox = [pygame.Rect(650, 230 + 30 * i, 250, 30) for i in range(len(ports_list))]

            # 绘制listbox
            for i, listbox_item in enumerate(default_listbox):
                pygame.draw.rect(input_screen, listbox_color, listbox_item)

            for i, listbox_item in enumerate(listbox):
                pygame.draw.rect(input_screen, listbox_color, listbox_item)
                if i == selected_index:
                    # 高亮选中串口
                    pygame.draw.rect(input_screen, (0, 0, 250), listbox_item)

            text = text_font.render("Available serial device:", True, (255, 255, 255))
            input_screen.blit(text, (650, 210))

            for i, comport in enumerate(ports_list):
                text = text_font.render(comport.device, True, (255, 255, 255))
                input_screen.blit(text, (650, 240 + 30 * i))
                if i == selected_index:
                    selected_port = comport

                    pygame.draw.rect(input_screen, listbox_color, default_listbox[0])
                    text = text_font.render(comport.device, True, (255, 255, 255))
                    input_screen.blit(text, (650, 210))

    for event in pygame.event.get():
        if event.type == pygloc.QUIT:
            return -1
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查鼠标是否在按钮上
            if quit_button.collidepoint(event.pos):
                return 0
            if select_com_button.collidepoint(event.pos):
                is_selecting_com_port = not is_selecting_com_port
                return 3
            if is_selecting_com_port:
                # 检查鼠标是否在某个listbox上
                if listbox is not None:
                    for i, listbox_item in enumerate(listbox):
                        if listbox_item.collidepoint(event.pos):
                            if selected_index != i:
                                selected_index = i
                            else:
                                selected_index = -1
                                if serial_port is not None:
                                    serial_port.close()
                                    serial_port = None
                                    selected_port = None
                                    control_handle = None

    # 没有特殊事件，返回本窗口对应的state码
    return state_code['auto_control_window']


# 绘制矩阵的函数，包括单元格值
def draw_matrix(surface, matrix, start_pos, cell_size):
    rows, cols = matrix.shape
    font = pygame.font.Font(None, 36)
    color = (128, 0, 255)

    for row in range(rows):
        for col in range(cols):
            cell_value = matrix[row, col]
            # 定义单元格的矩形
            rect = pygame.Rect(start_pos[0] + col * cell_size[0],
                               start_pos[1] + row * cell_size[1], cell_size[0], cell_size[1])

            # 绘制单元格边框
            pygame.draw.rect(surface, color, rect, 1)
            # 渲染单元格中的文本（保留两位小数）
            text_surf = font.render(f"{cell_value:.3f}", True, color)
            # 获取文本的大小以便居中对齐
            text_rect = text_surf.get_rect(center=rect.center)
            # 将文本绘制到屏幕上
            surface.blit(text_surf, text_rect)
