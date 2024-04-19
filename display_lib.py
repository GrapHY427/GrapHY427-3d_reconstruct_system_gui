import pygame

import communicate_lib


# display motor information on the GUI screen
def draw_motor_info(input_screen: pygame.Surface, text_font: pygame.font.Font, text_color: tuple,
                    width_and_height: tuple, step: int, input_control_handle: communicate_lib.ControlHandle or None):
    width, height = width_and_height

    if input_control_handle is not None:

        text = text_font.render(f"yaw speed: {input_control_handle.yaw_speed} rpm", True, text_color)
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"pitch speed: {input_control_handle.pitch_speed} rpm", True, text_color)
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"z_axis speed: {input_control_handle.z_axis_speed} rpm", True, text_color)
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"y_axis speed: {input_control_handle.y_axis_speed} rpm", True, text_color)
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"yaw angle: {int(input_control_handle.yaw_angle / 22.75)} degree", True, text_color)
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"pitch angle: {int(input_control_handle.pitch_angle)} degree", True, text_color)
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"z_axis position: {int(220 - input_control_handle.z_axis_position)} mm",
                                True, text_color)
        input_screen.blit(text, (width, height))
        height += step

        text = text_font.render(f"y_axis position: {int(310 - input_control_handle.y_axis_position)} mm",
                                True, text_color)
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
