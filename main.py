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
joystick: pygame.joystick.Joystick = None

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

control_handle: communicate_lib.ControlHandle = None
serial_port: serial.Serial = None

count = 0
joystick_control_flag = True
zero_position_flag = False
auto_control_flag = False

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
    global current_state_code

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

    for button in joystick_select_buttons:
        button.mouse_button_up_callback = do_nothing
        button_list.append(button)

    button1.mouse_button_up_callback = joystick_info_button_mouse_up_event_handler
    button2.mouse_button_up_callback = joystick_control_button_mouse_up_event_handler
    button3.mouse_button_up_callback = auto_control_button_mouse_up_event_handler
    button4.mouse_button_up_callback = quit_button_mouse_up_event_handler

    button_list.append(button1)
    button_list.append(button2)
    button_list.append(button3)
    button_list.append(button4)

    for button in button_list:
        button.set_mouse_on_color((0, 255, 255))
        button.set_mouse_down_color((0, 0, 255))
        button.mouse_motion_callback = mouse_on_event_handler
        button.mouse_button_down_callback = mouse_down_event_handler

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
                current_state_code = state_code['quit']
            for button in button_list:
                button.event_service(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
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

        if current_state_code != state_code['main_menu']:
            return


# 手柄信息监控窗口, state码: 1
def render_joystick_info_window(input_screen: pygame.surface.Surface, background: pygame.surface.Surface):
    global current_state_code
    global joystick

    # 注册标题
    title = display_lib.PackedText('Joystick Monitor', 60, (255, 255, 255), (450, 40))

    axis_text_list = []
    # # # 读取并显示每个轴的状态
    num_axes = joystick.get_numaxes()
    for i in range(num_axes):
        axis_text_list.append(display_lib.PackedText(f'Axis {i}: 0', 48, (0, 255, 255), (200, i * 90 + 100)))

    button_text_list = []
    # # 读取并显示每个按钮的状态
    num_buttons = joystick.get_numbuttons()
    for i in range(num_buttons):
        button_text_list.append(display_lib.PackedText(f'Button {i}', 48, (0, 255, 0), (850, i * 36 + 100)))

    # 设置按钮颜色
    button_color = (255, 255, 0)

    # 创建一个按钮
    button = display_lib.Button((490, 590), (200, 80), button_color, 'Main Menu', 42, (0, 0, 0), 25, 10)
    button.set_mouse_on_color((0, 255, 255))
    button.set_mouse_down_color((0, 0, 255))
    button.mouse_motion_callback = mouse_on_event_handler
    button.mouse_button_down_callback = mouse_down_event_handler
    button.mouse_button_up_callback = main_menu_button_mouse_up_event_handler

    while True:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygloc.QUIT:
                current_state_code = state_code['quit']
            button.event_service(event)

        for i, axis_text in enumerate(axis_text_list):
            axis = joystick.get_axis(i)
            if i < 4:
                axis = int(axis * 64)
            else:
                axis = int((axis + 1) * 128)
            axis_text.set_text(f'Axis {i}: {axis:d}')

        for i, button_text in enumerate(button_text_list):
            value = joystick.get_button(i)
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
def render_joystick_control_window(input_screen: pygame.surface.Surface, background: pygame.surface.Surface):
    global current_state_code

    global joystick
    global control_handle

    global frames
    global num_frames

    # 串口相关实例
    global selected_port
    global serial_port
    global selected_index
    global is_selecting_com_port

    previous_button_state = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    clear_window_flag = False

    # 注册标题
    joystick_control_text = display_lib.PackedText('Joystick Control', 60, (255, 255, 255), (450, 40))
    joystick_monitor_text = display_lib.PackedText('Joystick Monitor', 36, (0, 0, 255), (60, 120))
    motor_info_text = display_lib.PackedText('Motor Info', 36, (0, 0, 255), (320, 120))

    # 读取并显示每个轴的状态
    axis_text_list = []
    # # # 读取并显示每个轴的状态
    num_axes = joystick.get_numaxes()
    for i in range(num_axes):
        axis_text_list.append(display_lib.PackedText(f'Axis {i}: 0', 36, (0, 255, 255), (100, i * 40 + 170)))

    # 方便修改窗口位置相关参数
    button_color = (255, 255, 0)

    # 注册按钮
    quit_button = display_lib.Button(left_top=(490, 590), width_height=(200, 80), color=button_color, text='Main Menu',
                                     text_size=42, text_color=(0, 0, 0), text_horizon_offset=25, border_radius=10)
    select_com_button = display_lib.Button(left_top=(940, 200), width_height=(180, 40), color=button_color,
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
    quit_button.mouse_button_up_callback = main_menu_button_mouse_up_event_handler
    select_com_button.mouse_button_up_callback = select_com_button_mouse_button_up_event_handler
    y_axis_zero_button.mouse_button_up_callback = y_axis_zero_button_mouse_button_up_event_handler
    z_axis_zero_button.mouse_button_up_callback = z_axis_zero_button_mouse_button_up_event_handler
    pitch_zero_button.mouse_button_up_callback = pitch_zero_button_mouse_button_up_event_handler
    reset_frame_button.mouse_button_up_callback = reset_frame_button_mouse_button_up_event_handler
    save_frame_button.mouse_button_up_callback = save_frame_button_mouse_button_up_event_handler

    for button in button_list:
        button.mouse_motion_callback = mouse_on_event_handler
        button.mouse_button_down_callback = mouse_down_event_handler
        button.mouse_on_color = (0, 255, 255)
        button.mouse_down_color = (0, 0, 255)

    listbox = display_lib.ListBox(left_top=(675, 200), width_height=(260, 30), ordinary_color=(128, 128, 128),
                                  selected_color=(0, 255, 0), text_size=32, text_color=(255, 255, 255),
                                  text_horizon_offset=0, candidate_list=[], listbox_hint='Available Serial Device:',
                                  no_candidate_hint='No Serial Device!')
    listbox.set_mouse_down_color((0, 0, 255))
    listbox.set_mouse_on_color((0, 255, 255))
    listbox.mouse_button_up_callback = listbox_mouse_up_event_service
    listbox.mouse_button_down_callback = listbox_mouse_down_event_service
    listbox.mouse_motion_callback = listbox_mouse_on_event_service

    # 运行循环
    while True:
        for event in pygame.event.get():
            if event.type == pygloc.QUIT:
                current_state_code = state_code['quit']
            for button in button_list:
                button.event_service(event)
            listbox.process_event(event)

        # 填充背景
        input_screen.blit(background, (0, 0))

        # 初始化串口
        if selected_port is not None and serial_port is None:
            serial_port = serial.Serial(selected_port, baud_rate, timeout=time_out)
            control_handle = communicate_lib.ControlHandle()

        if selected_port is not None and serial_port is not None:
            if serial_port.name != selected_port:
                serial_port = serial.Serial(selected_port, baud_rate)

        if control_handle is not None:
            # 绘制状态指示文字
            serial_port_work_status_text.set_text(selected_port + ' work now')
            num_frames_count_text.set_text(f'Num frames: {num_frames}')

            transform_matrix_text.render(input_screen)

            transform_matrix = matrix_lib.compute_transform_matrix(
                [0,
                 ((220 - control_handle.z_axis_position) / 220),
                 (560 - control_handle.y_axis_position) / 560],
                [0, control_handle.pitch_angle, control_handle.yaw_angle / 22.76])

            transform_matrix_text.set_text('Transform Matrix')
            display_lib.draw_matrix(input_screen, transform_matrix, (630, 330), (70, 35))

            state, photo = camera.read()
            cv2.imshow('camera', photo)
            clear_window_flag = True

            # # 发送控制数据到MCU
            if (joystick.get_button(0) == 0) and (previous_button_state[0] == 1):
                if control_handle is not None:
                    io_lib.add_transform_matrix_to_frame(
                        dataset_dir + str(num_frames) + '.png', 0, transform_matrix, frames)
                    io_lib.capture_photo_to_dataset(photo_dir, num_frames, photo)
                    if state:
                        num_frames += 1
                    else:
                        io_lib.remove_last_transform_matrix_to_frame(frames)

            elif (joystick.get_button(3) == 0) and (previous_button_state[3] == 1):
                communicate_lib.send_play_music_command(serial_port)

            control_handle.get_joystick_signal(joystick)
            control_handle.send_speed_control_command(serial_port)
            control_handle.read_speed_control_report(serial_port, 0)
            for index in range(len(previous_button_state)):
                previous_button_state[index] = joystick.get_button(index)

        else:
            if clear_window_flag:
                cv2.destroyWindow('camera')
                clear_window_flag = False

            transform_matrix_text.set_text(' ')
            serial_port_work_status_text.set_text(' ')

        # 串口选择界面
        if is_selecting_com_port:
            candidate_list = []
            ports_list = list(serial.tools.list_ports.comports())

            for port in ports_list:
                candidate_list.append(port.name)

            listbox.update_candidate_list(candidate_list)

        # 读取手柄摇杆值
        for i, axis_text in enumerate(axis_text_list):
            axis = joystick.get_axis(i)
            if i < 4:
                axis = int(axis * 64)
            else:
                axis = int((axis + 1) * 128)
            axis_text.set_text(f'Axis {i}: {axis:d}')

        # 渲染控件
        display_lib.draw_motor_info(input_screen, 36, (0, 255, 0), (300, 170), 30, control_handle)
        for button in button_list:
            button.render(input_screen)
        for text in text_list:
            text.render(input_screen)
        for packed_text in axis_text_list:
            packed_text.render(input_screen)
        if is_selecting_com_port:
            listbox.render(input_screen)

        # 刷新屏幕
        pygame.display.flip()

        # 控制更新速率
        pygame.time.Clock().tick(60)

        # 如果状态码不在手柄控制上，则退出循环
        if current_state_code != state_code['joystick_control_window']:
            return


# 自动控制窗口, state码: 3
def render_auto_control_window(input_screen: pygame.surface.Surface, background: pygame.surface.Surface):
    global current_state_code

    global joystick
    global control_handle
    global joystick_control_flag
    global zero_position_flag

    global frames
    global num_frames

    # 串口相关实例
    global selected_port
    global serial_port
    global selected_index
    global is_selecting_com_port

    previous_button_state = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    clear_window_flag = False
    steady_state = 0

    # 注册标题
    joystick_control_text = display_lib.PackedText('Automated Control', 60, (255, 255, 255), (450, 40))
    joystick_monitor_text = display_lib.PackedText('Joystick Monitor', 36, (0, 0, 255), (60, 120))
    motor_info_text = display_lib.PackedText('Motor Info', 36, (0, 0, 255), (320, 120))
    auto_control_hint_text = display_lib.PackedText('Before auto control, Remember calibrate position encoder first',
                                                    36, (255, 255, 255), (280, 690))
    control_mode_hint_text = display_lib.PackedText(
        'Control mode: ' + ('  Joystick control' if joystick_control_flag else 'Automated control'),
        36, (0, 0, 255), (530, 120))

    # 读取并显示每个轴的状态
    axis_text_list = []
    # # # 读取并显示每个轴的状态
    num_axes = joystick.get_numaxes()
    for i in range(num_axes):
        axis_text_list.append(display_lib.PackedText(f'Axis {i}: 0', 36, (0, 255, 255), (100, i * 40 + 170)))

    # 方便修改窗口位置相关参数
    button_color = (255, 255, 0)

    # 注册按钮
    quit_button = display_lib.Button(left_top=(490, 590), width_height=(200, 80), color=button_color, text='Main Menu',
                                     text_size=42, text_color=(0, 0, 0), text_horizon_offset=25, border_radius=10)
    select_com_button = display_lib.Button(left_top=(940, 200), width_height=(180, 40), color=button_color,
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
    move_all_to_zero_button = display_lib.Button(left_top=(940, 450), width_height=(180, 40), color=button_color,
                                                 text='Move all to Zero', text_size=28, text_color=(0, 0, 0),
                                                 text_horizon_offset=15, border_radius=10)
    reset_frame_button = display_lib.Button(left_top=(940, 500), width_height=(180, 40), color=button_color,
                                            text='Reset Frame', text_size=28, text_color=(0, 0, 0),
                                            text_horizon_offset=30, border_radius=10)
    save_frame_button = display_lib.Button(left_top=(940, 550), width_height=(180, 40), color=button_color,
                                           text='Save Frame', text_size=28, text_color=(0, 0, 0),
                                           text_horizon_offset=30, border_radius=10)
    change_control_mode_button = display_lib.Button(left_top=(940, 110), width_height=(220, 40), color=button_color,
                                                    text='Change control mode', text_size=28, text_color=(0, 0, 0),
                                                    text_horizon_offset=5, border_radius=10)
    start_auto_sample_button = display_lib.Button(left_top=(150, 600), width_height=(210, 40), color=button_color,
                                                  text='Start Auto Sampling', text_size=28, text_color=(0, 0, 0),
                                                  text_horizon_offset=10, border_radius=10)

    # 注册提示用文字
    serial_port_work_status_text = display_lib.PackedText(' ', 36, (255, 255, 255), (650, 500))
    num_frames_count_text = display_lib.PackedText(' ', 28, (255, 255, 255), (950, 610))
    transform_matrix_text = display_lib.PackedText(' ', 28, (128, 0, 255), (650, 300))

    # 创建文字列表
    text_list = [joystick_control_text, joystick_monitor_text, motor_info_text,
                 serial_port_work_status_text, num_frames_count_text, transform_matrix_text,
                 auto_control_hint_text, control_mode_hint_text]

    text_list[0] = joystick_control_text
    text_list[1] = joystick_monitor_text
    text_list[2] = motor_info_text
    text_list[3] = serial_port_work_status_text
    text_list[4] = num_frames_count_text
    text_list[5] = transform_matrix_text
    text_list[6] = control_mode_hint_text

    # 创建按钮列表
    button_list = [quit_button, select_com_button, y_axis_zero_button, z_axis_zero_button, pitch_zero_button,
                   reset_frame_button, save_frame_button, move_all_to_zero_button, change_control_mode_button,
                   start_auto_sample_button]

    button_list[0] = quit_button
    button_list[1] = select_com_button
    button_list[2] = y_axis_zero_button
    button_list[3] = z_axis_zero_button
    button_list[4] = pitch_zero_button
    button_list[5] = reset_frame_button
    button_list[6] = save_frame_button
    button_list[7] = move_all_to_zero_button
    button_list[8] = change_control_mode_button
    button_list[9] = start_auto_sample_button

    for button in button_list:
        button.mouse_button_up_callback = do_nothing
        button.mouse_motion_callback = mouse_on_event_handler
        button.mouse_button_down_callback = mouse_down_event_handler
        button.mouse_on_color = (0, 255, 255)
        button.mouse_down_color = (0, 0, 255)

    # 注册回调函数
    quit_button.mouse_button_up_callback = main_menu_button_mouse_up_event_handler
    select_com_button.mouse_button_up_callback = select_com_button_mouse_button_up_event_handler
    y_axis_zero_button.mouse_button_up_callback = y_axis_zero_button_mouse_button_up_event_handler
    z_axis_zero_button.mouse_button_up_callback = z_axis_zero_button_mouse_button_up_event_handler
    pitch_zero_button.mouse_button_up_callback = pitch_zero_button_mouse_button_up_event_handler
    reset_frame_button.mouse_button_up_callback = reset_frame_button_mouse_button_up_event_handler
    save_frame_button.mouse_button_up_callback = save_frame_button_mouse_button_up_event_handler
    move_all_to_zero_button.mouse_button_up_callback = move_all_to_zero_button_mouse_button_up_event_handler
    change_control_mode_button.mouse_button_up_callback = change_control_mode_button_mouse_up_event_handler


    listbox = display_lib.ListBox(left_top=(675, 200), width_height=(260, 30), ordinary_color=(128, 128, 128),
                                  selected_color=(0, 255, 0), text_size=32, text_color=(255, 255, 255),
                                  text_horizon_offset=0, candidate_list=[], listbox_hint='Available Serial Device:',
                                  no_candidate_hint='No Serial Device!')
    listbox.set_mouse_down_color((0, 0, 255))
    listbox.set_mouse_on_color((0, 255, 255))
    listbox.mouse_button_up_callback = listbox_mouse_up_event_service
    listbox.mouse_button_down_callback = listbox_mouse_down_event_service
    listbox.mouse_motion_callback = listbox_mouse_on_event_service

    # 运行循环
    while True:
        for event in pygame.event.get():
            if event.type == pygloc.QUIT:
                current_state_code = state_code['quit']
            for button in button_list:
                button.event_service(event)
            listbox.process_event(event)

        control_mode_hint_text.set_text(
            'Control mode: ' + ('  Joystick control' if joystick_control_flag else 'Automated control'))

        # 填充背景
        input_screen.blit(background, (0, 0))

        # 初始化串口
        if selected_port is not None and serial_port is None:
            serial_port = serial.Serial(selected_port, baud_rate, timeout=time_out)
            control_handle = communicate_lib.ControlHandle()

        if selected_port is not None and serial_port is not None:
            if serial_port.name != selected_port:
                serial_port = serial.Serial(selected_port, baud_rate)

        if control_handle is not None:
            # 绘制状态指示文字
            serial_port_work_status_text.set_text(selected_port + ' work now')
            num_frames_count_text.set_text(f'Num frames: {num_frames}')

            transform_matrix_text.render(input_screen)

            transform_matrix = matrix_lib.compute_transform_matrix(
                [0,
                 ((220 - control_handle.z_axis_position) / 220),
                 (510 - control_handle.y_axis_position) / 510],
                [0, control_handle.pitch_angle, control_handle.yaw_angle / 22.76])

            transform_matrix_text.set_text('Transform Matrix')
            display_lib.draw_matrix(input_screen, transform_matrix, (630, 330), (70, 35))

            state, photo = camera.read()
            cv2.imshow('camera', photo)
            clear_window_flag = True

            # # 发送控制数据到MCU
            if joystick_control_flag:
                if (joystick.get_button(0) == 0) and (previous_button_state[0] == 1):
                    if control_handle is not None:
                        io_lib.add_transform_matrix_to_frame(
                            dataset_dir + str(num_frames) + '.png', 0, transform_matrix, frames)
                        io_lib.capture_photo_to_dataset(photo_dir, num_frames, photo)
                        if state:
                            num_frames += 1
                        else:
                            io_lib.remove_last_transform_matrix_to_frame(frames)

                elif (joystick.get_button(3) == 0) and (previous_button_state[3] == 1):
                    communicate_lib.send_play_music_command(serial_port)

                control_handle.get_joystick_signal(joystick)
                control_handle.send_speed_control_command(serial_port)
                control_handle.read_speed_control_report(serial_port, 0)
                for index in range(len(previous_button_state)):
                    previous_button_state[index] = joystick.get_button(index)
            else:
                control_handle.read_speed_control_report(serial_port, 1)
                if zero_position_flag:
                    if abs(control_handle.yaw_angle) < 20 and \
                            abs(control_handle.y_axis_position) < 2 and \
                            abs(control_handle.z_axis_position) < 2 and \
                            abs(control_handle.pitch_angle) < 2:  # abs(control_handle.yaw_angle) < 4
                        steady_state += 1

                    if steady_state > 5:
                        zero_position_flag = False
                        joystick_control_flag = True
                        steady_state = 0
                # 自动控制模式
                if auto_control_flag:
                    pass

        else:
            if clear_window_flag:
                cv2.destroyWindow('camera')
                clear_window_flag = False

            transform_matrix_text.set_text(' ')
            serial_port_work_status_text.set_text(' ')

        # 串口选择界面
        if is_selecting_com_port:
            candidate_list = []
            ports_list = list(serial.tools.list_ports.comports())

            for port in ports_list:
                candidate_list.append(port.name)

            listbox.update_candidate_list(candidate_list)

        # 读取手柄摇杆值
        for i, axis_text in enumerate(axis_text_list):
            axis = joystick.get_axis(i)
            if i < 4:
                axis = int(axis * 64)
            else:
                axis = int((axis + 1) * 128)
            axis_text.set_text(f'Axis {i}: {axis:d}')

        # 渲染控件
        display_lib.draw_motor_info(input_screen, 36, (0, 255, 0), (300, 170), 30, control_handle)
        for button in button_list:
            button.render(input_screen)
        for text in text_list:
            text.render(input_screen)
        for packed_text in axis_text_list:
            packed_text.render(input_screen)
        if is_selecting_com_port:
            listbox.render(input_screen)

        # 刷新屏幕
        pygame.display.flip()

        # 控制更新速率
        pygame.time.Clock().tick(60)

        # 如果状态码不在手柄控制上，则退出循环
        if current_state_code != state_code['auto_control_window']:
            return


def main_loop():
    global joystick
    global current_state_code

    current_state_code = state_code['main_menu']  # 0:主页面    1:手柄数据监测页面    2:手动控制滑台页面   3:自动控制滑台页面
    window_size = (1280, 720)  # 设置窗口大小
    running = True  # 游戏循环标志

    pygame.init()  # 初始化pygame
    pygame.joystick.init()  # 初始化游戏手柄

    screen = pygame.display.set_mode(window_size)  # 创建窗口
    pygame.display.set_caption("3D Reconstruction System")

    # pygame前端变量
    background = pygame.image.load('./data/background.jpg')
    background = pygame.transform.scale(background, window_size)
    background.set_alpha(255)

    # 游戏循环
    while running:

        if current_state_code == state_code['main_menu']:
            render_main_menu(screen, background)
            if pygame.joystick.get_count() <= 0 and (current_state_code == state_code['joystick_info_window'] or
                                                     current_state_code == state_code['joystick_control_window']):
                current_state_code = state_code['main_menu']
        elif current_state_code == state_code['joystick_info_window']:
            render_joystick_info_window(screen, background)
        elif current_state_code == state_code['joystick_control_window']:
            render_joystick_control_window(screen, background)
        elif current_state_code == state_code['auto_control_window']:
            render_auto_control_window(screen, background)
        else:
            pass
        if current_state_code == state_code['quit']:
            running = False

    # 退出pygame
    pygame.quit()


def do_nothing(input_button: display_lib.Button, input_event: pygame.event.Event):
    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.ordinary_color


def mouse_on_event_handler(input_button: display_lib.Button, input_event: pygame.event.Event):
    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
    else:
        input_button.color = input_button.ordinary_color


def mouse_down_event_handler(input_button: display_lib.Button, input_event: pygame.event.Event):
    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_down_color
    else:
        input_button.color = input_button.ordinary_color


def joystick_info_button_mouse_up_event_handler(input_button: display_lib.Button, input_event: pygame.event.Event):
    global current_state_code

    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        current_state_code = state_code['joystick_info_window']


def joystick_control_button_mouse_up_event_handler(input_button: display_lib.Button, input_event: pygame.event.Event):
    global current_state_code

    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        current_state_code = state_code['joystick_control_window']


def auto_control_button_mouse_up_event_handler(input_button: display_lib.Button, input_event: pygame.event.Event):
    global current_state_code

    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        current_state_code = state_code['auto_control_window']


def quit_button_mouse_up_event_handler(input_button: display_lib.Button, input_event: pygame.event.Event):
    global current_state_code

    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        current_state_code = state_code['quit']


def main_menu_button_mouse_up_event_handler(input_button: display_lib.Button, input_event: pygame.event.Event):
    global selected_index
    global serial_port
    global selected_port
    global control_handle
    global current_state_code
    global is_selecting_com_port

    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        selected_index = -1
        if serial_port is not None:
            serial_port.close()
            serial_port = None
            selected_port = None
            control_handle = None
            is_selecting_com_port = False
        current_state_code = state_code['main_menu']


def select_com_button_mouse_button_up_event_handler(input_button: display_lib.Button,
                                                    input_event: pygame.event.Event):
    global is_selecting_com_port

    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        is_selecting_com_port = not is_selecting_com_port


def y_axis_zero_button_mouse_button_up_event_handler(input_button: display_lib.Button,
                                                     input_event: pygame.event.Event):
    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        if serial_port is not None:
            communicate_lib.send_zero_y_axis_command(serial_port)


def z_axis_zero_button_mouse_button_up_event_handler(input_button: display_lib.Button,
                                                     input_event: pygame.event.Event):
    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        if serial_port is not None:
            communicate_lib.send_zero_z_axis_command(serial_port)


def pitch_zero_button_mouse_button_up_event_handler(input_button: display_lib.Button,
                                                    input_event: pygame.event.Event):
    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        if serial_port is not None:
            communicate_lib.send_zero_pitch_command(serial_port)


def reset_frame_button_mouse_button_up_event_handler(input_button: display_lib.Button,
                                                     input_event: pygame.event.Event):
    global frames
    global num_frames

    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        frames = []
        num_frames = 0


def save_frame_button_mouse_button_up_event_handler(input_button: display_lib.Button,
                                                    input_event: pygame.event.Event):
    global frames
    global num_frames

    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        io_lib.save_json_file(json_name, camera_angle_x, frames)
        frames = []
        num_frames = 0


def move_all_to_zero_button_mouse_button_up_event_handler(input_button: display_lib.Button,
                                                          input_event: pygame.event.Event):
    global control_handle
    global joystick_control_flag
    global zero_position_flag

    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        if control_handle is not None:
            control_handle.y_axis = 0
            control_handle.z_axis = 0
            control_handle.pitch = 0
            control_handle.yaw_pos = 0
            control_handle.send_position_control_command(serial_port)
            joystick_control_flag = False
            zero_position_flag = True


def change_control_mode_button_mouse_up_event_handler(input_button: display_lib.Button,
                                                      input_event: pygame.event.Event):
    global joystick_control_flag

    if input_button.button_rect.collidepoint(input_event.pos):
        input_button.color = input_button.mouse_on_color
        joystick_control_flag = not joystick_control_flag


def listbox_mouse_up_event_service(input_listbox: display_lib.ListBox):
    global serial_port
    global selected_port
    global control_handle

    if input_listbox.selected_index == -1:
        if serial_port is not None:
            serial_port.close()
            serial_port = None
            selected_port = None
            control_handle = None
    else:
        selected_port = input_listbox.candidate_list[input_listbox.selected_index]


def listbox_mouse_down_event_service(input_listbox: display_lib.ListBox):
    if input_listbox.selected_index == -1:
        pass


def listbox_mouse_on_event_service(input_listbox: display_lib.ListBox):
    if input_listbox.selected_index == -1:
        pass


if __name__ == '__main__':
    main_loop()
