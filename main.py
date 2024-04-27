import cv2
import pygame
import pygame.locals as pygloc
import serial.tools.list_ports

import communicate_lib
import display_lib
import matrix_lib
import io_lib

# 应用变量
joystick_index = -1
joystick = None

state_code = {'quit': -1, 'main_menu': 0, 'joystick_info_window': 1,
              'joystick_control_window': 2, 'auto_control_window': 3}

num_motor6020 = 1
num_motor2006 = 3

is_selecting_com_port = False
selected_index = -1
selected_port = None
baud_rate = 600000
time_out = 0.02

control_handle = None
serial_port = None

previous_button_state = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

count = 0

# 数据集相关全局变量
frames = []
num_frames = 0
json_name = './dataset/transform.json'
photo_dir = './dataset/photo/photo_'
dataset_dir = './photo/photo_'
camera_angle_x = 1.396

device_id = 0
camera = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))  # FOURCC编解码器的4个字符代码。
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 800)  # 宽度
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)  # 高度


# if not camera.isOpened():  # 检查摄像头是否成功打开
#     print("Failed to open camera")
# camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))  # FOURCC编解码器的4个字符代码。
# camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # 宽度
# camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)  # 高度
# camera.set(cv2.CAP_PROP_FPS, 60)  # 帧率 帧/秒
# camera.set(cv2.CAP_PROP_BRIGHTNESS, 5)  # 亮度 1
# camera.set(cv2.CAP_PROP_CONTRAST, 40)  # 对比度 40
# camera.set(cv2.CAP_PROP_SATURATION, 50)  # 饱和度 50
# camera.set(cv2.CAP_PROP_HUE, 40)  # 色调 50
# camera.set(cv2.CAP_PROP_EXPOSURE, 5)  # 曝光 50
# camera.set(cv2.CAP_PROP_CONVERT_RGB, 1)  # 表示图像是否应转换为RGB的布尔标志
# camera.set(cv2.CAP_PROP_RECTIFICATION, 1)  # 立体摄像机的整流标志（注意：只有当前支持DC1394 v 2.x后端）


# 主菜单, state码: 0
def render_main_menu(input_screen: pygame.surface.Surface, background: pygame.surface.Surface):
    global joystick
    global joystick_index

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
            joystick_index = 0
            joystick = pygame.joystick.Joystick(joystick_index)
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
        if i == joystick_index and pygame.joystick.get_count() > 0:
            # 高亮选中手柄
            pygame.draw.rect(input_screen, (0, 255, 0), button_item)

    for i in range(4):
        if i == joystick_index and pygame.joystick.get_count() > 0:
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
                        joystick_index = i
                        joystick = pygame.joystick.Joystick(joystick_index)
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

    global frames
    global num_frames

    global previous_button_state

    # 填充背景
    input_screen.fill((64, 64, 64))
    input_screen.blit(background, (0, 0))

    # 设置按钮颜色
    button_color = (255, 255, 0)

    listbox = None
    transform_matrix = None

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
    display_lib.draw_motor_info(input_screen, text_font, text_color, (width, height), step, control_handle)

    # 创建一个表示退出按钮的矩形
    quit_button = pygame.Rect(490, 590, 200, 80)
    select_com_button = pygame.Rect(900, 200, 180, 40)

    # 创建三个表示归零按钮的矩形
    y_axis_zero_button = pygame.Rect(940, 300, 180, 40)
    z_axis_zero_button = pygame.Rect(940, 350, 180, 40)
    pitch_zero_button = pygame.Rect(940, 400, 180, 40)

    # 创建三个表示归零按钮的矩形
    reset_frame_button = pygame.Rect(940, 500, 180, 40)
    save_frame_button = pygame.Rect(940, 550, 180, 40)

    # 绘制上文创建的圆角矩形按钮
    pygame.draw.rect(input_screen, button_color, select_com_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Select COM Port", True, (0, 0, 0))
    input_screen.blit(text, (910, 210))

    pygame.draw.rect(input_screen, button_color, y_axis_zero_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Zero Y Axis", True, (0, 0, 0))
    input_screen.blit(text, (970, 310))

    pygame.draw.rect(input_screen, button_color, z_axis_zero_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Zero Z Axis", True, (0, 0, 0))
    input_screen.blit(text, (970, 360))

    pygame.draw.rect(input_screen, button_color, pitch_zero_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Zero Pitch", True, (0, 0, 0))
    input_screen.blit(text, (970, 410))

    pygame.draw.rect(input_screen, button_color, reset_frame_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Reset Frame", True, (0, 0, 0))
    input_screen.blit(text, (970, 510))

    pygame.draw.rect(input_screen, button_color, save_frame_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Save Frame", True, (0, 0, 0))
    input_screen.blit(text, (970, 560))

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

            text_font = pygame.font.Font(None, 28)
            text = text_font.render(f"Num frames: {num_frames}", True, (255, 255, 255))
            input_screen.blit(text, (950, 610))

            text = text_font.render("Transform Matrix", True, (128, 0, 255))
            input_screen.blit(text, (650, 300))

            transform_matrix = matrix_lib.compute_transform_matrix(
                [0,
                 ((220 - control_handle.z_axis_position) / 220),
                 (510 - control_handle.y_axis_position) / 510],   # control_handle.z_axis_position / 220
                [0, control_handle.pitch_angle, control_handle.yaw_angle / 22.76])   # control_handle.yaw_angle

            display_lib.draw_matrix(input_screen, transform_matrix, (630, 330), (70, 35))

        state, photo = camera.read()
        cv2.imshow('camera', photo)

        # # 发送控制数据到MCU
        if (input_joystick.get_button(0) == 0) and (previous_button_state[0] == 1):
            if control_handle is not None:
                io_lib.add_transform_matrix_to_frame(
                    dataset_dir + str(num_frames) + '.png', 0, transform_matrix, frames)
                io_lib.capture_photo_to_dataset(photo_dir, num_frames, photo)
                if state:
                    num_frames += 1
                else:
                    io_lib.remove_last_transform_matrix_to_frame(frames)

        elif (input_joystick.get_button(3) == 0) and (previous_button_state[3] == 1):
            communicate_lib.send_play_music_command(serial_port)

        for index in range(len(previous_button_state)):
            previous_button_state[index] = input_joystick.get_button(index)

        if control_handle is not None:
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
                return state_code['main_menu']
            if select_com_button.collidepoint(event.pos):
                is_selecting_com_port = not is_selecting_com_port
                return state_code['joystick_control_window']
            if y_axis_zero_button.collidepoint(event.pos):
                if serial_port is not None:
                    communicate_lib.send_zero_y_axis_command(serial_port)
            if z_axis_zero_button.collidepoint(event.pos):
                if serial_port is not None:
                    communicate_lib.send_zero_z_axis_command(serial_port)
            if pitch_zero_button.collidepoint(event.pos):
                if serial_port is not None:
                    communicate_lib.send_zero_pitch_command(serial_port)
            if reset_frame_button.collidepoint(event.pos):
                frames = []
                num_frames = 0
            if save_frame_button.collidepoint(event.pos):
                io_lib.save_json_file(json_name, camera_angle_x, frames)
                frames = []
                num_frames = 0
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
    text_font = pygame.font.Font(None, 36)
    global selected_index
    global is_selecting_com_port
    global control_handle

    global frames
    global num_frames

    global previous_button_state

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
    text = title_font.render(f"Automated Control", True, (255, 255, 255))
    input_screen.blit(text, (450, 40))

    text = text_font.render(f"Motor Info", True, (255, 255, 255))
    input_screen.blit(text, (320, 120))

    # 方便修改窗口位置相关参数
    width = 300
    height = 200
    step = 30
    text_color = (0, 255, 0)

    # # 读取并显示每个电机的状态
    display_lib.draw_motor_info(input_screen, text_font, text_color, (width, height), step, control_handle)

    # 创建一个表示退出按钮的矩形
    quit_button = pygame.Rect(490, 590, 200, 80)
    select_com_button = pygame.Rect(900, 200, 180, 40)

    # 创建三个表示归零按钮的矩形
    y_axis_zero_button = pygame.Rect(940, 300, 180, 40)
    z_axis_zero_button = pygame.Rect(940, 350, 180, 40)
    pitch_zero_button = pygame.Rect(940, 400, 180, 40)

    # 创建三个表示归零按钮的矩形
    reset_frame_button = pygame.Rect(940, 500, 180, 40)
    save_frame_button = pygame.Rect(940, 550, 180, 40)

    # 绘制上文创建的圆角矩形按钮
    pygame.draw.rect(input_screen, button_color, select_com_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Select COM Port", True, (0, 0, 0))
    input_screen.blit(text, (910, 210))

    pygame.draw.rect(input_screen, button_color, y_axis_zero_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Zero Y Axis", True, (0, 0, 0))
    input_screen.blit(text, (970, 310))

    pygame.draw.rect(input_screen, button_color, z_axis_zero_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Zero Z Axis", True, (0, 0, 0))
    input_screen.blit(text, (970, 360))

    pygame.draw.rect(input_screen, button_color, pitch_zero_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Zero Pitch", True, (0, 0, 0))
    input_screen.blit(text, (970, 410))

    pygame.draw.rect(input_screen, button_color, reset_frame_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Reset Frame", True, (0, 0, 0))
    input_screen.blit(text, (970, 510))

    pygame.draw.rect(input_screen, button_color, save_frame_button, border_radius=10)
    text_font = pygame.font.Font(None, 28)
    text = text_font.render(f"Save Frame", True, (0, 0, 0))
    input_screen.blit(text, (970, 560))

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

            text_font = pygame.font.Font(None, 28)
            text = text_font.render(f"Num frames: {num_frames}", True, (255, 255, 255))
            input_screen.blit(text, (950, 610))

            text = text_font.render("Transform Matrix", True, (128, 0, 255))
            input_screen.blit(text, (650, 300))

            transform_matrix = matrix_lib.compute_transform_matrix(
                [0,
                 -1,
                 -2],  # control_handle.z_axis_position / 220
                [90, control_handle.pitch_angle, control_handle.yaw_angle])  # control_handle.yaw_angle

            display_lib.draw_matrix(input_screen, transform_matrix, (630, 330), (70, 35))

        state, photo = camera.read()
        cv2.imshow('camera', photo)

        # # 发送控制数据到MCU
        if control_handle is not None:

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
                return state_code['main_menu']
            if select_com_button.collidepoint(event.pos):
                is_selecting_com_port = not is_selecting_com_port
                return state_code['auto_control_window']
            if y_axis_zero_button.collidepoint(event.pos):
                if serial_port is not None:
                    communicate_lib.send_zero_y_axis_command(serial_port)
            if z_axis_zero_button.collidepoint(event.pos):
                if serial_port is not None:
                    communicate_lib.send_zero_z_axis_command(serial_port)
            if pitch_zero_button.collidepoint(event.pos):
                if serial_port is not None:
                    communicate_lib.send_zero_pitch_command(serial_port)
            if reset_frame_button.collidepoint(event.pos):
                frames = []
                num_frames = 0
            if save_frame_button.collidepoint(event.pos):
                io_lib.save_json_file(json_name, camera_angle_x, frames)
                frames = []
                num_frames = 0
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


def main_loop():
    global joystick

    # 初始化pygame
    pygame.init()

    # 设置窗口大小
    window_size = (1280, 720)

    # 创建窗口
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption("3D Reconstruction System")

    # 初始化游戏手柄
    pygame.joystick.init()

    # pygame前端变量
    background = pygame.image.load('./data/background.jpg')
    background = pygame.transform.scale(background, window_size)
    background.set_alpha(255)

    state = 0  # 0:主页面    1:手柄数据监测页面    2:手动控制滑台页面   3:自动控制滑台页面

    # 游戏循环标志
    running = True

    # 游戏循环
    while running:

        if state == state_code['main_menu']:
            state, joystick = render_main_menu(screen, background)
            if pygame.joystick.get_count() <= 0 and (state == 1 or state == 2):
                state = state_code['main_menu']
        elif state == state_code['joystick_info_window']:
            state = render_joystick_info_window(screen, background, joystick)
        elif state == state_code['joystick_control_window']:
            state = render_joystick_control_window(screen, background, joystick)
        elif state == state_code['auto_control_window']:
            state = render_auto_control_window(screen, background)
        else:
            pass

        if state == state_code['quit']:
            running = False

        # 刷新屏幕
        pygame.display.flip()

        # 控制更新速率
        pygame.time.Clock().tick(60)

    # 退出pygame
    pygame.quit()


if __name__ == '__main__':
    main_loop()
