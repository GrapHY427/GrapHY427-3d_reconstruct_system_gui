import numpy as np
import json
import cv2


def add_transform_matrix_to_frame(filepath: str, rotation_deg: float, transform_matrix: np.ndarray, frames: list):
    dictionary = {"file_path": filepath,
                  "rotation": np.deg2rad(rotation_deg),
                  "transform_matrix": transform_matrix.tolist()}
    frames.append(dictionary)


def remove_last_transform_matrix_to_frame(frames: list):
    frames.pop()


def save_json_file(filename: str, camera_angle_x: float, frames: list):
    dictionary = {"camera_angle_x": camera_angle_x, "frames": frames}
    with open(filename, "w+") as f:
        json.dump(dictionary, f)


def open_camera(device_id: int = 0):
    camera = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)
    if not camera.isOpened():  # 检查摄像头是否成功打开
        print("Failed to open camera")
    return camera


def capture_photo_to_dataset(filepath: str, number: int, photo: np.ndarray):
    photo_format = '.png'
    filename = filepath + str(number) + photo_format
    cv2.imwrite(filename, photo)
