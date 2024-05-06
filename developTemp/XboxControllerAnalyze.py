import pygame
import pygame.locals as pygloc

import numpy as np
# import serial
import display_lib


def euler_to_rotation_matrix(roll, pitch, yaw):
    """
    Convert Euler angles (in degrees) to a camera_rotation matrix.
    """
    # Convert angles to radians
    roll = np.deg2rad(roll)
    pitch = np.deg2rad(pitch)
    yaw = np.deg2rad(yaw)

    # Compute camera_rotation matrix around x-axis (roll)
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(roll), -np.sin(roll)],
                    [0, np.sin(roll), np.cos(roll)]])

    # Compute camera_rotation matrix around y-axis (camera_pitch)
    R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                    [0, 1, 0],
                    [-np.sin(pitch), 0, np.cos(pitch)]])

    # Compute camera_rotation matrix around z-axis (camera_yaw)
    R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                    [np.sin(yaw), np.cos(yaw), 0],
                    [0, 0, 1]])

    # Combined camera_rotation matrix
    R = np.dot(R_z, np.dot(R_y, R_x))
    return R


def compute_camera_extrinsic_matrix(position, rotation):
    """
    Compute the camera extrinsic matrix from camera_position and camera_rotation (Euler angles).
    """
    # Extract camera_position and camera_rotation
    x, y, z = position
    roll, pitch, yaw = rotation

    # Compute camera_rotation matrix from Euler angles
    R = euler_to_rotation_matrix(roll, pitch, yaw)

    # Translation vector
    t = np.array([x, y, z])

    # Construct the extrinsic matrix
    matrix = np.eye(4)
    matrix[:3, :3] = R
    matrix[:3, 3] = t

    return matrix


# 绘制矩阵的函数，包括单元格值
def draw_matrix(surface, matrix, start_pos, cell_size):
    rows, cols = matrix.shape
    for row in range(rows):
        for col in range(cols):
            cell_value = matrix[row, col]
            # 定义单元格的矩形
            rect = pygame.Rect(start_pos[0] + col * cell_size[0],
                               start_pos[1] + row * cell_size[1], cell_size[0], cell_size[1])
            # 填充单元格背景
            pygame.draw.rect(surface, (0, 0, 0), rect)
            # 绘制单元格边框
            pygame.draw.rect(surface, (255, 255, 255), rect, 1)
            # 渲染单元格中的文本（保留两位小数）
            text_surf = font.render(f"{cell_value:.2f}", True, (255, 255, 255))
            # 获取文本的大小以便居中对齐
            text_rect = text_surf.get_rect(center=rect.center)
            # 将文本绘制到屏幕上
            surface.blit(text_surf, text_rect)


def mouse_on_event(button: display_lib.Button, input_event: pygame.event.Event):
    if button.button_rect.collidepoint(input_event.pos):
        button.color = (255, 0, 0)
    else:
        button.color = (255, 255, 0)


# Example usage

# 初始化pygame
pygame.init()

# 设置窗口大小
window_size = (800, 600)

# 创建窗口
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Joystick Tester")

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
z_axis = 0.0
camera_position = [0, 0, 1]  # Position of the camera in world coordinates
camera_rotation = [0, 0, 0]  # Rotation of the camera in Euler angles (roll, camera_pitch, camera_yaw)

confirm_button = display_lib.Button()
confirm_button.set_attribute((200, 200), (150, 50), (255, 255, 0), 'button', 36, (0, 0, 0), 33, 10)
confirm_button.mouse_motion = mouse_on_event

# 游戏循环
while running:
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygloc.QUIT:
            running = False
        if event.type == pygame.MOUSEMOTION:
            confirm_button.mouse_motion(confirm_button, event)

    # 填充背景
    screen.fill((0, 0, 0))

    # # 读取并显示每个轴的状态
    num_axes = joystick.get_numaxes()
    for i in range(num_axes):
        axis = joystick.get_axis(i)
        # if i < 4:
        #     axis = int(axis * 1024)
        # else:
        #     axis = int((axis + 1) * 128)
        # text = font.render(f"Axis {i}: {axis:d}", True, (255, 255, 255))
        text = font.render(f"Axis {i}: {axis:.4f}", True, (255, 255, 255))
        screen.blit(text, (20, i * 30 + 20))
    #
    # # 读取并显示每个按钮的状态
    # num_buttons = joystick.get_numbuttons()
    # for i in range(num_buttons):
    #     button = joystick.get_button(i)
    #     text = font.render(f"Button {i}: {button}", True, (255, 255, 255))
    #     screen.blit(text, (400, i * 30 + 20))
    j += 1

    if j > 10:
        j = 0
    camera_yaw -= (joystick.get_axis(4) + 1) * 0.8
    camera_yaw += (joystick.get_axis(5) + 1) * 0.8
    camera_pitch -= joystick.get_axis(3) if abs(joystick.get_axis(3)) > 0.05 else 0
    y_axis -= joystick.get_axis(1) * 0.01 if abs(joystick.get_axis(1)) > 0.05 else 0
    z_axis += joystick.get_axis(0) * 0.01 if abs(joystick.get_axis(1)) > 0.05 else 0
    camera_yaw %= 360
    camera_pitch = max(-90.0, min(camera_pitch, 90.0))
    y_axis = max(0.0, min(y_axis, 1.0))
    z_axis = max(0.0, min(z_axis, 1.0))

    camera_rotation[2] = camera_yaw
    camera_rotation[1] = camera_pitch

    camera_position[1] = y_axis
    camera_position[0] = np.sin(np.deg2rad(camera_yaw)) * z_axis
    camera_position[2] = np.cos(np.deg2rad(camera_yaw)) * z_axis

    extrinsic_matrix = compute_camera_extrinsic_matrix(camera_position, camera_rotation)
    draw_matrix(screen, np.array([camera_position]), (400, 0), (100, 50))
    draw_matrix(screen, np.array([camera_rotation]), (400, 100), (100, 50))
    draw_matrix(screen, extrinsic_matrix, (400, 250), (100, 50))

    confirm_button.render(screen)

    # 刷新屏幕
    pygame.display.flip()

    # 控制更新速率
    pygame.time.Clock().tick(60)

# 退出pygame
pygame.quit()
