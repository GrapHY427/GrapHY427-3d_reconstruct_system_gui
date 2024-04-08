import numpy as np
import matrix_lib
import json


frames = []
for angle in range(360):
    transform_matrix: np.ndarray = matrix_lib.compute_transform_matrix([0, 0.5, 1], [0, 0, angle])
    dictionary = {"file_path": "./data/r_" + str(int(angle)),
                  "rotation": np.deg2rad(angle),
                  "transform_matrix": transform_matrix.tolist()}
    frames.append(dictionary)
data = {"camera_angle_x": 0.6911112070083618, "frames": frames}
filename = '../dataset/' + 'transform' + '.json'
with open(filename, "w+") as f:
    json.dump(data, f)
