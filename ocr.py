# import paddle
from flask import Flask, request, jsonify, abort
from paddleocr import PaddleOCR
import os
import uuid
import PyPDF2
import base64
import requests
from PIL import Image
import io

# gpu_available = paddle.device.is_compiled_with_cuda()
# print("GPU available:", gpu_available)

app = Flask(__name__)
# gongdj server
# ocr = PaddleOCR(use_angle_cls=True, use_gpu=True, det=False)
ocr = PaddleOCR(use_angle_cls=False, lang="ch", use_gpu=False, det=False, enable_mkldnn=True, cpu_threads=8)
# ocr服务器
# ocr = PaddleOCR(use_gpu=False, det=False, enable_mkldnn=True, cpu_threads=8)

@app.route('/api/ocr', methods=['POST'])
def ocr_on_pdf_or_image():
    if 'file' not in request.files:
        return Result("", "没有需要OCR的文件", 500)

    # 获取上传的文件和页码参数
    file = request.files['file']
    page_num = int(request.form.get('page_num', 0))

    # 获取名为 'param' 的 POST 参数，如果参数不存在则默认值为 'check'
    ocrType = request.form.get('ocrType')
    need_angle = int(request.form.get('need_angle', 0))

    if ocrType not in ['check', 'compare']:
        return Result("", "ocrType参数必须为check或compare", 500)

    if ocrType == 'check':
        ocrTypeAlias = "文档合规性检查OCR识别"
    elif ocrType == 'compare':
        ocrTypeAlias = "文档比对OCR识别"

    # 保存文件到临时目录
    # 获取当前运行Python文件所在目录的tmp子目录
    current_dir = os.getcwd()
    tmp_dir = os.path.join(current_dir, 'tmp')

    # 如果tmp目录不存在，则创建
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    file_extension = os.path.splitext(file.filename)[1].lower()

    # 生成一个随机的UUID
    random_uuid = uuid.uuid4()

    # 将UUID转换为字符串
    uuid_str = str(random_uuid)
    # 保存文件到临时目录
    file_path = os.path.join(tmp_dir, uuid_str + '' + file_extension)
    correct_image_angle_path = os.path.join(tmp_dir, uuid_str + '_correct' + file_extension)

    remove_stamp_image_path = os.path.join(tmp_dir, uuid_str + '_remove_stamp' + file_extension)

    print(f"ori filename={file.filename}, file_path={file_path}, ocrType={ocrTypeAlias}")
    file.save(file_path)
    file.save(correct_image_angle_path)
    file.save(remove_stamp_image_path)

    try:
        if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
            # OCR on single image
            ocr.page_num = 0

            if need_angle == 1:
                # 图片矫正
                correct_image_angle(file_path, correct_image_angle_path)
                # 签章消除
                # ocr_remove_stamp.remove_stamp(correct_image_angle_path,remove_stamp_image_path)

                result = ocr.ocr(correct_image_angle_path, cls=False, det=True)
            else:
                result = ocr.ocr(file_path, cls=False, det=True)

        elif file_extension == '.pdf':
            ocr.page_num = page_num
            # ocr.page_num = 0

            # page = get_pdf_page(file_path, page_num)
            # save_page_as_pdf(page, output_file_path)

            result = ocr.ocr(file_path, cls=False, det=True)

            # print(f'ori filename={file.filename}, 文件file_path:{file_path}, OCR成功, OCR出来的内容为：{result}')
            # print(f'ori filename={file.filename}, 文件file_path:{file_path}, OCR成功')

            # # 删除临时文件
            # os.remove(file_path)
            #
            # dataObj = get_object(result, ocrType)
            #
            # return Result(dataObj, "success", 200)

        else:
            print(f'文件:{file.filename}, {file_extension} ocr不支持')
            # 删除临时文件
            os.remove(file_path)
            os.remove(correct_image_angle_path)
            os.remove(remove_stamp_image_path)
            return Result("", "当前文件格式不支持", 500)

        print(f'ori filename={file.filename}, 文件file_path:{file_path}, OCR成功')

        # 删除临时文件
        os.remove(file_path)
        os.remove(correct_image_angle_path)
        os.remove(remove_stamp_image_path)

        dataObj = get_object(result, ocrType)

        return Result(dataObj, "success", 200)
        # return Result(result, "success", 200)

    except Exception as e:
        print(f'文件:{file.filename}, OCR异常：{str(e)}')
        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
            os.remove(correct_image_angle_path)
            os.remove(remove_stamp_image_path)
            print(f'ori filename={file.filename}, 文件:{file_path}, 已删除')
        else:
            print(f'ori filename={file.filename}, 文件:{file_path}, 文件不存在, 不再执行删除操作')

        return Result("", str(e), 500)

    # # 删除临时文件
    # os.remove(file_path)
    #
    # dataObj = get_object(result, ocrType)
    #
    # return Result(dataObj, "success", 200)

# 图像矫正
def correct_image_angle(file_path, correct_image_angle_path):
    url = "http://172.16.32.49:11111/correct_angle"
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
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

def Result(data=None, message="success", code=200):
    return jsonify({
        "code": code,
        "message": message,
        "data": data
    }), code


def get_object(data, ocrType):
    if ocrType == 'check':
        result = ""
    elif ocrType == 'compare':
        result = []

    if data is None:
        print('ocr识别出来的内容为空')
        result = ""
        return result

    if isinstance(data, list):

        if ocrType == 'check':
            for item in data:
                if item is None:
                    continue

                for subitem in item:
                    if isinstance(subitem, list) and len(subitem) >= 2 and len(subitem[1]) >= 1:
                        result = result + "" + subitem[1][0]
        elif ocrType == 'compare':
            result = sort.ocr_sort(data[0])

    return result

def get_pdf_page(file_path, page_number):
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfFileReader(file)
        if page_number < pdf_reader.numPages:
            page = pdf_reader.getPage(page_number - 1)
            return page
        else:
            print("页码超出范围")
            return None

def save_page_as_pdf(page, output_file_path):
    pdf_writer = PyPDF2.PdfFileWriter()
    pdf_writer.addPage(page)
    with open(output_file_path, 'wb') as output_file:
        pdf_writer.write(output_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7018)
