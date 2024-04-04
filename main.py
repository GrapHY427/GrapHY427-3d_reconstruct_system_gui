import pygame

import display_lib
# import matrix_lib


# 初始化pygame
pygame.init()

# 设置窗口大小
window_size = (1280, 720)

# 创建窗口
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("3D Reconstruction System")

# 初始化游戏手柄
pygame.joystick.init()
joystick = None

# pygame前端变量
background = pygame.image.load('./data/background.jpg')
background = pygame.transform.scale(background, window_size)
background.set_alpha(255)

state = 0          # 0:主页面    1:手柄数据监测页面    2:手动控制滑台页面   3:自动控制滑台页面

# 设置字体用于显示文本
text_font = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 48)

# 游戏循环标志
running = True

# 应用变量
selected_joystick = None

state_code = display_lib.state_code

camera_pitch = 0.0
camera_yaw = 0.0
y_axis = 0.0
camera_position = [0, 0, 1]  # Position of the camera in world coordinates
camera_rotation = [0, 0, 0]  # Rotation of the camera in Euler angles (roll, camera_pitch, camera_yaw)

# 游戏循环
while running:

    if state == state_code['main_menu']:
        state, joystick = display_lib.render_main_menu(screen, background)
        if pygame.joystick.get_count() <= 0 and (state == 1 or state == 2):
            state = state_code['main_menu']
    elif state == state_code['joystick_info_window']:
        state = display_lib.render_joystick_info_window(screen, background, joystick)
    elif state == state_code['joystick_control_window']:
        state = display_lib.render_joystick_control_window(screen, background, joystick)
    elif state == state_code['auto_control_window']:
        state = display_lib.render_auto_control_window(screen, background)
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
