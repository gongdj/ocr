import cv2
import requests
import base64
from PIL import Image
import io

def remove_stamp(stamp_image_path, remove_stamp_image_path):
    invoice_file_name = "remove_stamp"
    # ori_image_path = "F:\\ideaPycharmProjects\\studyPy\\tmp\\stamp.png"
    # 读取文件
    img = cv2.imread(stamp_image_path, cv2.IMREAD_COLOR)
    if img is None:
        print("无法读取图像文件，请检查文件路径和格式是否正确。")
        return  # 或者采取其他错误处理方式
    print(img.shape)
    # 对图片进行三通道分离，得到三个通道文件
    B_channel, G_channel, R_channel = cv2.split(img)  # 注意cv2.split()返回通道顺序
    _, RedThresh = cv2.threshold(R_channel, 170, 355, cv2.THRESH_BINARY)
    # cv2.imwrite('F:\\ideaPycharmProjects\\studyPy\\tmp\\RedThresh_{}.jpg'.format(invoice_file_name), RedThresh)
    cv2.imwrite(remove_stamp_image_path, RedThresh)
    # return "success"

def remove_stamp_remote(stamp_image_path, remove_stamp_image_path):
    url = "http://172.26.4.55:7096/rmStamp4Pdf"
    with open(stamp_image_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            json_data = response.json()
            if json_data["code"] == "200":
                img_data = base64.b64decode(json_data["pdfb64"])
                img = Image.open(io.BytesIO(img_data))
                # img.save("corrected_image.jpg")
                img.save(remove_stamp_image_path)
                print("图片消除签章成功，已保存为", remove_stamp_image_path)
            else:
                print("图片消除签章失败，错误信息：", json_data["message"])
        else:
            print("请求失败，状态码：", response.status_code)