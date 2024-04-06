import numpy as np


def euler_to_rotation_matrix(roll, pitch, yaw):
    """
    Convert Euler angles (in degrees) to a camera_rotation matrix.
    """
    # Convert angles to radians
    roll = np.deg2rad(roll)
    pitch = np.deg2rad(pitch)
    yaw = np.deg2rad(yaw)

    # Compute camera_rotation matrix around x-axis (roll)
    R_x = np.array([[np.cos(roll), -np.sin(roll), 0],
                    [np.sin(roll), np.cos(roll), 0],
                    [0, 0, 1]])

    # Compute camera_rotation matrix around y-axis (camera_pitch)
    R_y = np.array([[np.cos(pitch), 0, -np.sin(pitch)],
                    [0, 1, 0],
                    [np.sin(pitch), 0, np.cos(pitch)]])

    # Compute camera_rotation matrix around z-axis (camera_yaw)
    R_z = np.array([[1, 0, 0],
                    [0, np.cos(yaw), -np.sin(yaw)],
                    [0, np.sin(yaw), np.cos(yaw)]])

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
