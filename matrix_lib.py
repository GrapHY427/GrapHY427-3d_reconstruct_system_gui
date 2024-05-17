import math

import numpy as np


def euler_to_rotation_matrix(euler_angles):
    """
    将欧拉角转换为旋转矩阵
    :param euler_angles: 相机的欧拉角（yaw, pitch, roll）
    :return: 3x3 旋转矩阵
    """
    yaw, pitch, roll = euler_angles
    yaw = np.deg2rad(yaw)
    pitch = np.deg2rad(pitch)
    roll = np.deg2rad(roll)
    # 计算旋转矩阵
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(roll), -np.sin(roll)],
                    [0, np.sin(roll), np.cos(roll)]])
    R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                    [0, 1, 0],
                    [-np.sin(pitch), 0, np.cos(pitch)]])
    R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                    [np.sin(yaw), np.cos(yaw), 0],
                    [0, 0, 1]])
    rotation_matrix = R_x @ R_y @ R_z
    return rotation_matrix


def compute_transform_matrix(position, euler_angles):
    """
    计算相机的外参矩阵
    :param position: 相机在世界坐标系中的位置（x, y, z）
    :param euler_angles: 相机的欧拉角（yaw, pitch, roll）
    :return: 4x4 外参矩阵
    """
    # rotation_matrix = euler_to_rotation_matrix(euler_angles)
    # translation_vector = np.array(position).reshape(3, 1)
    # extrinsic_matrix = np.hstack((rotation_matrix, translation_vector))
    # extrinsic_matrix = np.vstack((extrinsic_matrix, [0, 0, 0, 1]))
    x, y, z = position
    roll, pitch, yaw = euler_angles
    pitch = np.deg2rad(pitch)
    yaw = np.deg2rad(yaw)
    return pose_spherical(yaw, pitch, 3 * 0.5)


trans_t = lambda t: np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, t],
    [0, 0, 0, 1]])

rot_phi = lambda phi: np.array([
    [1, 0, 0, 0],
    [0, np.cos(phi), -np.sin(phi), 0],
    [0, np.sin(phi), np.cos(phi), 0],
    [0, 0, 0, 1]])

rot_theta = lambda theta: np.array([
    [np.cos(theta), 0, -np.sin(theta), 0],
    [0, 1, 0, 0],
    [np.sin(theta), 0, np.cos(theta), 0],
    [0, 0, 0, 1]])


def pose_spherical(theta, phi, radius):
    c2w = trans_t(radius)
    c2w = rot_phi(phi) @ c2w
    c2w = rot_theta(theta) @ c2w
    c2w = np.array([[-1, 0, 0, 0],
                    [0, 0, 1, 0],
                    [0, 1, 0, 0],
                    [0, 0, 0, 1]]) @ c2w
    return c2w
