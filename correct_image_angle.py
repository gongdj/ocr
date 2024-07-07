import cv2
from paddleocr import PaddleOCR, draw_ocr
import numpy as np
import base64
import requests
from PIL import Image
import io
import time

def correct_image_angle(file_path, correct_image_angle_path):
    url = "http://172.16.32.49:11111/correct_angle" # 测试
    # url = "http://172.16.5.61:11111/correct_angle"  # 生产

    # 记录开始时间
    start_time = time.time()

    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)

        # 记录结束时间
        end_time = time.time()
        # 计算接口调用耗时
        elapsed_time = end_time - start_time
        print(f"[图片校正]-接口调用耗时: {elapsed_time:.2f} 秒")

        if response.status_code == 200:
            json_data = response.json()
            if json_data["code"] == "200":
                img_data = base64.b64decode(json_data["imgb64"])
                img = Image.open(io.BytesIO(img_data))
                # img.save("corrected_image.jpg")
                img.save(correct_image_angle_path)
                print("图片矫正成功，已保存为", correct_image_angle_path)
            else:
                print("图片矫正失败，错误信息：", json_data["message"])
        else:
            print("请求失败，状态码：", response.status_code)

# 使用方法：request_image_correction("your_image_path.jpg")


def jz_image():
    # 读取待矫正的图片
    image_path = 'D:\\aaa.jpg'
    # img = cv2.imread(image_path)

    # 初始化 PaddleOCR
    ocr = PaddleOCR()

    # 读取图像
    # image_path = 'your_image.jpg'
    image = cv2.imread(image_path)

    # 使用 PaddleOCR 进行文本检测
    result = ocr.ocr(image, cls=False)

    # 解析检测结果，获取文本框
    boxes = [item[0] for line in result for item in line]

    # 提取文本框的四个角点，并转换为八个坐标点
    rotated_images = []
    for box in boxes:
        x_min, y_min = np.min(box, axis=0)
        x_max, y_max = np.max(box, axis=0)

        x1, y1 = x_min, y_min
        x2, y2 = x_max, y_min
        x3, y3 = x_max, y_max
        x4, y4 = x_min, y_max

        # 计算旋转角度
        angle = np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi

        # 矫正图像
        rotated = cv2.warpAffine(image, cv2.getRotationMatrix2D((x1, y1), angle, 1.0), (image.shape[1], image.shape[0]))

        rotated_images.append(rotated)

    # 显示和保存矫正后的图像
    # for i, rotated in enumerate(rotated_images):
    #     cv2.imshow(f"Rotated {i}", rotated)
    #     cv2.imwrite(f'rotated_image_{i}.jpg', rotated)
    #
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

if __name__ == "__main__":
    jz_image()