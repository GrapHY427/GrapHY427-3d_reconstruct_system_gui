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

current_state_code = state_code['main_menu']

num_motor6020 = 1
num_motor2006 = 3

is_selecting_com_port = False
selected_index = -1
selected_port = None
baud_rate = 600000
time_out = 0.02

control_handle = None
serial_port: serial.Serial = None

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


# 主菜单, state码: 0
def render_main_menu(input_screen: pygame.surface.Surface, background: pygame.surface.Surface):
    global joystick
    global joystick_index

    button_list = []

    # 注册标题
    title = display_lib.PackedText('3D Reconstruction System', 72, (255, 255, 255), (350, 40))

    # 设置按钮颜色
    button_color = (255, 255, 0)

    # 注册按钮
    button1 = display_lib.Button(
        left_top=(360, 200), width_height=(250, 80), color=button_color, text='Joystick Monitor', text_size=36,
        text_color=(0, 0, 0), text_horizon_offset=25, border_radius=10)
    button2 = display_lib.Button(
        left_top=(720, 200), width_height=(250, 80), color=button_color, text='Joystick Control', text_size=36,
        text_color=(0, 0, 0), text_horizon_offset=30, border_radius=10)
    button3 = display_lib.Button(
        left_top=(360, 400), width_height=(250, 80), color=button_color, text='Automated Control', text_size=36,
        text_color=(0, 0, 0), text_horizon_offset=10, border_radius=10)
    button4 = display_lib.Button(
        left_top=(720, 400), width_height=(250, 80), color=button_color, text='QUIT', text_size=36,
        text_color=(0, 0, 0), text_horizon_offset=85, border_radius=10)

    # 注册手柄选择按钮
    joystick_select_buttons = [display_lib.Button(
        left_top=(50 + 300 * i, 600), width_height=(250, 80), color=button_color, text='No Joystick', text_size=36,
        text_color=(0, 0, 0), text_horizon_offset=50, border_radius=10) for i in range(4)]

    select_joystick_hint = display_lib.PackedText(
        'Select a joystick, if no joystick connected, some function will be disabled', 32, (255, 255, 255), (250, 560))

    button_list.append(button1)
    button_list.append(button2)
    button_list.append(button3)
    button_list.append(button4)
    for button in joystick_select_buttons:
        button_list.append(button)

    for button in button_list:
        button.set_mouse_on_color((0, 255, 255))
        button.mouse_motion_callback = mouse_on_event_handler

    # 运行过程
    while True:
        if joystick is None:
            if pygame.joystick.get_count() > 0:  # 尝试初始化手柄
                joystick_index = 0
                joystick = pygame.joystick.Joystick(joystick_index)
                joystick.init()
        if pygame.joystick.get_count() <= 0:
            button1.ordinary_color = (128, 128, 128)
            button2.ordinary_color = (128, 128, 128)

            button1.set_mouse_on_color((128, 128, 128))
            button2.set_mouse_on_color((128, 128, 128))
        else:
            button1.ordinary_color = button_color
            button2.ordinary_color = button_color

            button1.set_mouse_on_color((0, 255, 255))
            button2.set_mouse_on_color((0, 255, 255))

        for i in range(4):
            if i == joystick_index and pygame.joystick.get_count() > 0:
                # 更改显示文字
                joystick_select_buttons[i].text = f'Joystick {i} Selected'
                joystick_select_buttons[i].text_horizon_offset = 10
            elif i < pygame.joystick.get_count():
                joystick_select_buttons[i].text = f'Joystick {i} Available'
                joystick_select_buttons[i].text_horizon_offset = 10
            else:
                joystick_select_buttons[i].text = f'No Joystick'
                joystick_select_buttons[i].text_horizon_offset = 32

        # 绘制手柄选择窗口
        for i, button_item in enumerate(joystick_select_buttons):
            if i == joystick_index and pygame.joystick.get_count() > 0:
                # 高亮选中手柄
                joystick_select_buttons[i].ordinary_color = (0, 255, 0)
                joystick_select_buttons[i].text_horizon_offset = 10
            else:
                joystick_select_buttons[i].ordinary_color = button_color
                joystick_select_buttons[i].text_horizon_offset = 50

        # 处理事件
        for event in pygame.event.get():
            if event.type == pygloc.QUIT:
                return state_code['quit'], joystick
            if event.type == pygame.MOUSEMOTION:
                for button in button_list:
                    button.mouse_motion_callback(button, event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 检查鼠标是否在按钮1上
                if button1.button_rect.collidepoint(event.pos) and pygame.joystick.get_count() > 0:
                    return state_code['joystick_info_window'], joystick
                # 检查鼠标是否在按钮2上
                elif button2.button_rect.collidepoint(event.pos) and pygame.joystick.get_count() > 0:
                    return state_code['joystick_control_window'], joystick
                # 检查鼠标是否在按钮3上
                elif button3.button_rect.collidepoint(event.pos):
                    return state_code['auto_control_window'], joystick
                # 检查鼠标是否在按钮4上
                elif button4.button_rect.collidepoint(event.pos):
                    return state_code['quit'], joystick
                for i, button in enumerate(joystick_select_buttons):
                    if button.button_rect.collidepoint(event.pos):
                        if i < pygame.joystick.get_count():
                            joystick_index = i
                            joystick = pygame.joystick.Joystick(joystick_index)
                            joystick.init()

        # 填充背景
        input_screen.blit(background, (0, 0))
        # 渲染标题
        title.render(input_screen)
        # 渲染按钮
        for button in button_list:
            button.render(input_screen)
        # 渲染文字
        select_joystick_hint.render(input_screen)
        # 刷新屏幕
        pygame.display.flip()
        # 控制更新速率
        pygame.time.Clock().tick(60)


# 手柄信息监控窗口, state码: 1
def render_joystick_info_window(input_screen: pygame.surface.Surface, background: pygame.surface.Surface,
                                input_joystick: pygame.joystick.Joystick):
    global current_state_code

    # 注册标题
    title = display_lib.PackedText('Joystick Monitor', 60, (255, 255, 255), (450, 40))

    axis_text_list = []
    # # # 读取并显示每个轴的状态
    num_axes = input_joystick.get_numaxes()
    for i in range(num_axes):
        axis_text_list.append(display_lib.PackedText(f'Axis {i}: 0', 48, (0, 255, 255), (200, i * 90 + 100)))

    button_text_list = []
    # # 读取并显示每个按钮的状态
    num_buttons = input_joystick.get_numbuttons()
    for i in range(num_buttons):
        button_text_list.append(display_lib.PackedText(f'Button {i}', 48, (0, 255, 0), (850, i * 36 + 100)))

    # 设置按钮颜色
    button_color = (255, 255, 0)

    # 创建一个按钮
    button = display_lib.Button((490, 590), (200, 80), button_color, 'Main Menu', 42, (0, 0, 0), 25, 10)
    button.set_mouse_on_color((0, 255, 255))
    button.mouse_motion_callback = mouse_on_event_handler

    while True:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygloc.QUIT:
                current_state_code = state_code['quit']
            if event.type == pygame.MOUSEMOTION:
                button.mouse_motion_callback(button, event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 检查鼠标是否在按钮上
                if button.button_rect.collidepoint(event.pos):
                    current_state_code = state_code['main_menu']

        for i, axis_text in enumerate(axis_text_list):
            axis = input_joystick.get_axis(i)
            if i < 4:
                axis = int(axis * 64)
            else:
                axis = int((axis + 1) * 128)
            axis_text.set_text(f'Axis {i}: {axis:d}')

        for i, button_text in enumerate(button_text_list):
            value = input_joystick.get_button(i)
            if value == 0:
                button_text.set_color((0, 255, 0))
            else:
                button_text.set_color((255, 0, 0))

        # 渲染背景
        input_screen.blit(background, (0, 0))

        # 渲染各个控件
        title.render(input_screen)
        button.render(input_screen)
        for packed_text in axis_text_list:
            packed_text.render(input_screen)
        for packed_text in button_text_list:
            packed_text.render(input_screen)

        # 刷新屏幕
        pygame.display.flip()

        # 控制更新速率
        pygame.time.Clock().tick(60)

        if current_state_code != state_code['joystick_info_window']:
            return


# 手柄控制窗口, state码: 2
def render_joystick_control_window(input_screen: pygame.surface.Surface, background: pygame.surface.Surface,
                                   input_joystick: pygame.joystick.Joystick):

    global current_state_code

    global selected_index
    global is_selecting_com_port
    global control_handle

    global frames
    global num_frames

    global previous_button_state

    # 串口相关实例
    global selected_port
    global serial_port

    listbox = None
    transform_matrix = None

    # 注册标题
    joystick_control_text = display_lib.PackedText('Joystick Control', 60, (255, 255, 255), (450, 40))
    joystick_monitor_text = display_lib.PackedText('Joystick Monitor', 36, (255, 255, 255), (60, 120))
    motor_info_text = display_lib.PackedText('Motor Info', 36, (255, 255, 255), (320, 120))

    # 读取并显示每个轴的状态
    axis_text_list = []
    # # # 读取并显示每个轴的状态
    num_axes = input_joystick.get_numaxes()
    for i in range(num_axes):
        axis_text_list.append(display_lib.PackedText(f'Axis {i}: 0', 36, (0, 255, 255), (100, i * 50 + 200)))

    # 方便修改窗口位置相关参数
    width = 300
    height = 200
    step = 30
    text_color = (0, 255, 0)
    button_color = (255, 255, 0)

    # 注册按钮
    quit_button = display_lib.Button(left_top=(490, 590), width_height=(200, 80), color=button_color, text='Main Menu',
                                     text_size=42, text_color=(0, 0, 0), text_horizon_offset=25, border_radius=10)
    select_com_button = display_lib.Button(left_top=(900, 200), width_height=(180, 40), color=button_color,
                                           text='Select COM Port', text_size=28, text_color=(0, 0, 0),
                                           text_horizon_offset=10, border_radius=10)
    y_axis_zero_button = display_lib.Button(left_top=(940, 300), width_height=(180, 40), color=button_color,
                                            text='Zero Y Axis', text_size=28, text_color=(0, 0, 0),
                                            text_horizon_offset=30, border_radius=10)
    z_axis_zero_button = display_lib.Button(left_top=(940, 350), width_height=(180, 40), color=button_color,
                                            text='Zero Z Axis', text_size=28, text_color=(0, 0, 0),
                                            text_horizon_offset=30, border_radius=10)
    pitch_zero_button = display_lib.Button(left_top=(940, 400), width_height=(180, 40), color=button_color,
                                           text='Zero Pitch', text_size=28, text_color=(0, 0, 0),
                                           text_horizon_offset=30, border_radius=10)
    reset_frame_button = display_lib.Button(left_top=(940, 500), width_height=(180, 40), color=button_color,
                                            text='Reset Frame', text_size=28, text_color=(0, 0, 0),
                                            text_horizon_offset=30, border_radius=10)
    save_frame_button = display_lib.Button(left_top=(940, 550), width_height=(180, 40), color=button_color,
                                           text='Save Frame', text_size=28, text_color=(0, 0, 0),
                                           text_horizon_offset=30, border_radius=10)

    # 注册提示用文字
    serial_port_work_status_text = display_lib.PackedText(' ', 36, (255, 255, 255), (650, 500))
    num_frames_count_text = display_lib.PackedText(' ', 28, (255, 255, 255), (950, 610))
    transform_matrix_text = display_lib.PackedText(' ', 28, (128, 0, 255), (650, 300))

    # 创建文字列表
    text_list = [joystick_control_text, joystick_monitor_text, motor_info_text, serial_port_work_status_text,
                 num_frames_count_text, transform_matrix_text]

    text_list[0] = joystick_control_text
    text_list[1] = joystick_monitor_text
    text_list[2] = motor_info_text
    text_list[3] = serial_port_work_status_text
    text_list[4] = num_frames_count_text
    text_list[5] = transform_matrix_text

    # 创建按钮列表
    button_list = [quit_button, select_com_button, y_axis_zero_button, z_axis_zero_button, pitch_zero_button,
                   reset_frame_button, save_frame_button]
    button_list[0] = quit_button
    button_list[1] = select_com_button
    button_list[2] = y_axis_zero_button
    button_list[3] = z_axis_zero_button
    button_list[4] = pitch_zero_button
    button_list[5] = reset_frame_button
    button_list[6] = save_frame_button

    # 注册回调函数
    quit_button.mouse_button_down_callback = quit_button_mouse_button_down_event_handler
    select_com_button.mouse_button_down_callback = select_com_button_mouse_button_down_event_handler
    y_axis_zero_button.mouse_button_down_callback = y_axis_zero_button_mouse_button_down_event_handler
    z_axis_zero_button.mouse_button_down_callback = z_axis_zero_button_mouse_button_down_event_handler
    pitch_zero_button.mouse_button_down_callback = pitch_zero_button_mouse_button_down_event_handler
    reset_frame_button.mouse_button_down_callback = reset_frame_button_mouse_button_down_event_handler
    save_frame_button.mouse_button_down_callback = save_frame_button_mouse_button_down_event_handler

    for button in button_list:
        button.mouse_motion_callback = mouse_on_event_handler
        button.mouse_on_color = (0, 255, 255)

    # 运行循环
    while True:
        for event in pygame.event.get():
            if event.type == pygloc.QUIT:
                current_state_code = state_code['main_menu']
            for button in button_list:
                button.event_service(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
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

        # 填充背景
        input_screen.blit(background, (0, 0))

        # 初始化串口
        if selected_port is not None and serial_port is None:
            serial_port = serial.Serial(selected_port.name, baud_rate, timeout=time_out)
            control_handle = communicate_lib.ControlHandle()

        if selected_port is not None and serial_port is not None:
            if serial_port.name != selected_port.name:
                serial_port = serial.Serial(selected_port.name, baud_rate)

            if control_handle is not None:
                # 绘制状态指示文字
                serial_port_work_status_text.set_text(selected_port.name + ' work now')
                serial_port_work_status_text.render(input_screen)

                num_frames_count_text.set_text(f'Num frames: {num_frames}')
                serial_port_work_status_text.render(input_screen)

                transform_matrix_text.render(input_screen)

                transform_matrix = matrix_lib.compute_transform_matrix(
                    [0,
                     ((220 - control_handle.z_axis_position) / 220),
                     (510 - control_handle.y_axis_position) / 510],
                    [0, control_handle.pitch_angle, control_handle.yaw_angle / 22.76])

                transform_matrix_text.set_text('Transform Matrix')
                display_lib.draw_matrix(input_screen, transform_matrix, (630, 330), (70, 35))
            else:
                transform_matrix_text.set_text(' ')

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

        # 读取手柄摇杆值
        for i, axis_text in enumerate(axis_text_list):
            axis = input_joystick.get_axis(i)
            if i < 4:
                axis = int(axis * 64)
            else:
                axis = int((axis + 1) * 128)
            axis_text.set_text(f'Axis {i}: {axis:d}')

        # 渲染控件
        display_lib.draw_motor_info(input_screen, 36, text_color, (width, height), step, control_handle)
        for button in button_list:
            button.render(input_screen)
        for text in text_list:
            text.render(input_screen)
        for packed_text in axis_text_list:
            packed_text.render(input_screen)

        # 刷新屏幕
        pygame.display.flip()

        # 控制更新速率
        pygame.time.Clock().tick(60)

        # 如果状态码不在手柄控制上，则退出循环
        if current_state_code != state_code['joystick_control_window']:
            return


# 自动控制窗口, state码: 3
def render_auto_control_window(input_screen: pygame.surface.Surface, background: pygame.surface.Surface):
    pass


def main_loop():
    global joystick
    global current_state_code

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

    current_state_code = state_code['main_menu']  # 0:主页面    1:手柄数据监测页面    2:手动控制滑台页面   3:自动控制滑台页面

    # 游戏循环标志
    running = True

    # 游戏循环
    while running:

        if current_state_code == state_code['main_menu']:
            current_state_code, joystick = render_main_menu(screen, background)
            if pygame.joystick.get_count() <= 0 and (current_state_code == 1 or current_state_code == 2):
                current_state_code = state_code['main_menu']
        elif current_state_code == state_code['joystick_info_window']:
            render_joystick_info_window(screen, background, joystick)
        elif current_state_code == state_code['joystick_control_window']:
            render_joystick_control_window(screen, background, joystick)
        elif current_state_code == state_code['auto_control_window']:
            render_auto_control_window(screen, background)
        else:
            pass

        if current_state_code == state_code['quit']:
            running = False

    # 退出pygame
    pygame.quit()


def mouse_on_event_handler(input_button: display_lib.Button, input_event: pygame.event.Event):
    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
    else:
        input_button.color = input_button.ordinary_color


def quit_button_mouse_button_down_event_handler(input_button: display_lib.Button, input_event: pygame.event.Event):
    global selected_index
    global serial_port
    global selected_port
    global control_handle
    global current_state_code

    if input_button.button_rect.collidepoint(input_event.pos):
        selected_index = -1
        if serial_port is not None:
            serial_port.close()
            serial_port = None
            selected_port = None
            control_handle = None
        current_state_code = state_code['main_menu']


def select_com_button_mouse_button_down_event_handler(input_button: display_lib.Button,
                                                      input_event: pygame.event.Event):
    global is_selecting_com_port

    if input_button.button_rect.collidepoint(input_event.pos):
        is_selecting_com_port = not is_selecting_com_port


def y_axis_zero_button_mouse_button_down_event_handler(input_button: display_lib.Button,
                                                       input_event: pygame.event.Event):
    if input_button.button_rect.collidepoint(input_event.pos):
        if serial_port is not None:
            communicate_lib.send_zero_y_axis_command(serial_port)


def z_axis_zero_button_mouse_button_down_event_handler(input_button: display_lib.Button,
                                                       input_event: pygame.event.Event):
    if input_button.button_rect.collidepoint(input_event.pos):
        if serial_port is not None:
            communicate_lib.send_zero_z_axis_command(serial_port)


def pitch_zero_button_mouse_button_down_event_handler(input_button: display_lib.Button,
                                                      input_event: pygame.event.Event):
    if input_button.button_rect.collidepoint(input_event.pos):
        if serial_port is not None:
            communicate_lib.send_zero_pitch_command(serial_port)


def reset_frame_button_mouse_button_down_event_handler(input_button: display_lib.Button,
                                                       input_event: pygame.event.Event):
    global frames
    global num_frames

    if input_button.button_rect.collidepoint(input_event.pos):
        frames = []
        num_frames = 0


def save_frame_button_mouse_button_down_event_handler(input_button: display_lib.Button,
                                                      input_event: pygame.event.Event):
    global frames
    global num_frames

    if input_button.button_rect.collidepoint(input_event.pos):
        io_lib.save_json_file(json_name, camera_angle_x, frames)
        frames = []
        num_frames = 0


if __name__ == '__main__':
    main_loop()
