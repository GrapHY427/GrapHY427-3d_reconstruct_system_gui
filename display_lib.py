import pygame

import communicate_lib


# display motor information on the GUI screen
def draw_motor_info(input_screen: pygame.Surface, text_size: int, text_color: tuple,
                    width_height: tuple, step: int, input_control_handle: communicate_lib.ControlHandle or None):

    width, height = width_height

    if input_control_handle is not None:

        sentence_list = [
            f'yaw speed: {input_control_handle.yaw_speed} rpm',
            f'pitch speed: {input_control_handle.pitch_speed} rpm',
            f'z_axis speed: {input_control_handle.z_axis_speed} rpm',
            f'y_axis speed: {input_control_handle.y_axis_speed} rpm',
            f'yaw angle: {int(input_control_handle.yaw_angle / 22.75)} degree',
            f'pitch angle: {int(input_control_handle.pitch_angle)} degree',
            f'z_axis position: {int(input_control_handle.z_axis_position)} mm',
            f'y_axis position: {int(input_control_handle.y_axis_position)} mm']
    else:
        sentence_list = [
            f'yaw speed: None',
            f'pitch speed: None',
            f'z_axis speed: None',
            f'y_axis speed: None',
            f'yaw angle: None',
            f'pitch angle: None',
            f'z_axis position: None',
            f'y_axis position: None']

    for sentence in sentence_list:
        text_font = pygame.font.Font(None, text_size)
        text = text_font.render(sentence, True, text_color)
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


class Button:
    left_top = (100, 100)
    width_height = (30, 20)
    button_rect = None
    color = (128, 128, 128)
    ordinary_color = (128, 128, 128)
    mouse_on_color = (128, 128, 128)
    text = 'Button'
    text_size = 10
    text_font = None
    text_height = 13.278
    text_color = (0, 0, 0)
    text_horizon_offset = 0
    text_vertical_offset = 0
    border_radius = 0

    # callback function
    mouse_motion_callback = None
    mouse_button_down_callback = None
    mouse_button_up_callback = None

    def __init__(self, left_top: tuple, width_height: tuple, color: tuple, text: str, text_size: int,
                 text_color: tuple, text_horizon_offset: int, border_radius: int = 0):
        self.left_top = left_top
        self.width_height = width_height
        self.button_rect = pygame.Rect(self.left_top, self.width_height)
        self.color = color
        self.ordinary_color = color
        self.mouse_on_color = self.ordinary_color
        self.mouse_down_color = self.ordinary_color
        self.text = text
        self.text_size = text_size
        self.text_font = pygame.font.Font(None, text_size)
        self.text_height = 0.62 * text_size  # round(1.3278 * text_size)
        self.text_color = text_color
        self.text_horizon_offset = text_horizon_offset
        self.text_vertical_offset = (self.width_height[1] - self.text_height) / 2
        self.border_radius = border_radius

    def set_text_size(self, text_size):
        self.text_size = text_size
        self.text_font = pygame.font.Font(None, text_size)

    def set_mouse_on_color(self, mouse_on_color: tuple):
        self.mouse_on_color = mouse_on_color

    def set_mouse_down_color(self, mouse_down_color: tuple):
        self.mouse_down_color = mouse_down_color

    def render(self, input_screen: pygame.surface.Surface):
        pygame.draw.rect(input_screen, self.color, self.button_rect, border_radius=self.border_radius)
        text = self.text_font.render(self.text, True, self.text_color)
        input_screen.blit(text, (self.left_top[0] + self.text_horizon_offset,
                                 self.left_top[1] + self.text_vertical_offset))

    def register_event_function(self, event: int, callback_function: staticmethod):
        if event == pygame.MOUSEMOTION:
            self.mouse_motion_callback = callback_function
        elif event == pygame.MOUSEBUTTONDOWN:
            self.mouse_button_down_callback = callback_function
        elif event == pygame.MOUSEBUTTONUP:
            self.mouse_button_up_callback = callback_function

    def event_service(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self.mouse_motion_callback(self, event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_button_down_callback(self, event)
        elif event.type == pygame.MOUSEBUTTONUP:
            pass
            self.mouse_button_up_callback(self, event)
        else:
            pass


class PackedText:
    def __init__(self, text: str, size: int, color: tuple, left_top: tuple):
        self.text = text
        self.size = size
        self.font = pygame.font.Font(None, size)
        self.color = color
        self.left_top = left_top

    def set_color(self, color):
        self.color = color

    def set_text(self, text):
        self.text = text

    def set_size(self, size):
        self.size = size
        self.font = pygame.font.Font(None, size)

    def set_position(self, left_top):
        self.left_top = left_top

    def render(self, input_screen: pygame.surface.Surface):
        rendered_text = self.font.render(self.text, True, self.color)
        input_screen.blit(rendered_text, self.left_top)


class ListBox:
    def __init__(self, left_top: tuple, width_height: tuple, ordinary_color: tuple, selected_color: tuple,
                 triangle_color: tuple, text_size: int, text_color: int, text_horizon_offset: int,
                 candidate_list: list, listbox_hint: str, no_candidate_hint: str):
        self.left_top = left_top
        self.left, self.top = left_top
        self.width_height = width_height
        self.width, self.height = width_height
        self.ordinary_color = ordinary_color
        self.selected_color = selected_color
        self.triangle_color = triangle_color
        self.text_size = text_size
        self.text_height = 0.62 * text_size
        self.text_color = text_color
        self.text_horizon_offset = text_horizon_offset
        self.text_vertical_offset = (self.width_height[1] - self.text_height) / 2
        self.candidate_list = candidate_list
        self.selected_index = -1
        self.previous_selected_index = -1
        self.listbox_hint = listbox_hint
        self.no_candidate_text = no_candidate_hint

        # 回调函数
        self.listbox_selected_callback = None
        self.listbox_cancel_selected_callback = None
        self.listbox_auto_select_callback = None
        self.mouse_motion_callback = None
        self.mouse_button_down_callback = None
        self.mouse_button_up_callback = None

    def set_selected_index(self, selected_index: int):
        self.previous_selected_index = self.selected_index
        self.selected_index = selected_index

    def cancel_selected_index(self):
        self.selected_index = -1

    def update_candidate_list(self, candidate_list: list):
        self.candidate_list = candidate_list

    def process_event(self, input_event: pygame.event.Event):
        if input_event.type == pygame.MOUSEMOTION:
            self.mouse_motion_callback(self, input_event)
        elif input_event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_button_down_callback(self, input_event)
        elif input_event.type == pygame.MOUSEBUTTONUP:
            self.mouse_button_up_callback(self, input_event)

    def render(self, input_screen: pygame.surface.Surface):
        text_font = pygame.font.Font(None, self.text_size)
        listbox_list = [pygame.Rect(self.left_top, self.width_height)]

        if len(self.candidate_list) <= 0:
            # 绘制listbox
            for i, listbox_item in enumerate(listbox_list):
                pygame.draw.rect(input_screen, self.ordinary_color, listbox_item)

            text = text_font.render(self.no_candidate_text, True, self.text_color)
            input_screen.blit(text, (self.left + self.text_horizon_offset, self.top + self.text_vertical_offset))
        else:
            # 创建一个表示listbox的列表
            listbox = [pygame.Rect((self.left, self.top + self.height * i), self.width_height)
                       for i in range(len(self.candidate_list))]

            # 绘制listbox
            for i, listbox_item in enumerate(listbox_list):
                pygame.draw.rect(input_screen, self.ordinary_color, listbox_item)

            for i, listbox_item in enumerate(listbox):
                pygame.draw.rect(input_screen, self.ordinary_color, listbox_item)
                if i == self.selected_index:
                    # 高亮选中选项
                    pygame.draw.rect(input_screen, self.selected_color, listbox_item)

            text = text_font.render(self.listbox_hint, True, self.text_color)
            input_screen.blit(text, (self.left + self.text_horizon_offset, self.top + self.text_vertical_offset))

            for i, comport in enumerate(self.candidate_list):
                text = text_font.render(comport.device, True, self.text_color)
                input_screen.blit(text, (self.left + self.text_horizon_offset,
                                         self.top + self.text_vertical_offset + self.height * i))
