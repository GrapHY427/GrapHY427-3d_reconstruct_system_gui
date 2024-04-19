import cv2

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not camera.isOpened():  # 检查摄像头是否成功打开
    print("Failed to open camera")
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))  # FOURCC编解码器的4个字符代码。
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 600)  # 宽度
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)  # 高度
# camera.set(cv2.CAP_PROP_FPS, 25)  # 帧率 帧/秒
# camera.set(cv2.CAP_PROP_BRIGHTNESS, 1)  # 亮度 1
# camera.set(cv2.CAP_PROP_CONTRAST, 50)  # 对比度 40
# camera.set(cv2.CAP_PROP_SATURATION, 50)  # 饱和度 50
# camera.set(cv2.CAP_PROP_HUE, 50)  # 色调 50
# camera.set(cv2.CAP_PROP_EXPOSURE, 50)  # 曝光 50
# camera.set(cv2.CAP_PROP_POS_AVI_RATIO, 0)  # 视频文件的相对位置：0-胶片开始，1-胶片结束。
# camera.set(cv2.CAP_PROP_CONVERT_RGB, 1)  # 表示图像是否应转换为RGB的布尔标志
# camera.set(cv2.CAP_PROP_RECTIFICATION, 1)  # 立体摄像机的整流标志（注意：只有当前支持DC1394 v 2.x后端）
# camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

while camera.isOpened():
    ret, frame = camera.read()  # 读取摄像头画面
    cv2.imshow('video', frame)  # 显示画面
    key = cv2.waitKey(10)
    # 按Q退出
    if key & 0xFF == ord('q'):
        break
camera.release()  # 释放摄像头
cv2.destroyAllWindows()  # 释放所有显示图像窗口
