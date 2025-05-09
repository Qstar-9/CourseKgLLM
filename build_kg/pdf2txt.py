from paddleocr import PaddleOCR, draw_ocr
import fitz  # PyMuPDF 用于获取PDF的页数和转换为图像
from PIL import Image
import cv2
import numpy as np
import os

# 设置PDF文件夹路径
pdf_folder_path = '/media/zhjk/rmx/tails_cls/tcm_pdf/edupdf'  # 这里是PDF文件夹路径
pdf_test="推理模型与普通大模型的区别分析.pdf"
# 获取文件夹中所有PDF文件
pdf_files = [f for f in os.listdir(pdf_folder_path) if f.endswith('.pdf')]

# 初始化OCR模型
ocr = PaddleOCR(use_angle_cls=True, lang="ch")

def pdf_txt(pdf_folder_path,pdf_test):
    pdf_file = os.path.join(pdf_folder_path, pdf_test)

    print(f"正在处理文件: {pdf_file}")
    
    # 使用fitz打开PDF，获取总页数
    with fitz.open(pdf_file) as pdf:
        PAGE_NUM = pdf.page_count  # 获取实际页数

    # 识别PDF文件
    result = ocr.ocr(pdf_file, cls=True)
    
    # 打开文本文件，用于保存识别结果
    txt_file_path = f'ocr_res/{pdf_test.split(".pdf")[0]}.txt'  # 保存文本文件
    print(txt_file_path)
    with open(txt_file_path, 'w', encoding='utf-8') as f:
        for idx in range(len(result)):
            res = result[idx]
            if res is None:  # 跳过识别结果为空的页面
                print(f"[DEBUG] Empty page {idx + 1} detected, skip it.")
                continue

            f.write(f"---- Page {idx + 1} ----\n")  # 保存页码信息

            for line in res:
                txt = line[1][0]  # 获取文本
                f.write(txt + "\n")  # 将文本写入文件

    # 处理PDF页面并保存图片
    imgs = []
    with fitz.open(pdf_file) as pdf:
        for pg in range(0, PAGE_NUM):
            page = pdf[pg]
            mat = fitz.Matrix(2, 2)
            pm = page.get_pixmap(matrix=mat, alpha=False)
            # 如果宽度或高度大于2000像素，不放大图像
            if pm.width > 2000 or pm.height > 2000:
                pm = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
            img = Image.frombytes("RGB", [pm.width, pm.height], pm.samples)
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            imgs.append(img)

    # 绘制并保存每一页的OCR识别结果
    for idx in range(len(result)):
        res = result[idx]
        if res is None:
            continue
        image = imgs[idx]
        boxes = [line[0] for line in res]
        txts = [line[1][0] for line in res]
        scores = [line[1][1] for line in res]
        
        # 绘制识别框和文本
        im_show = draw_ocr(image, boxes, txts, scores, font_path='doc/fonts/simfang.ttf')
        im_show = Image.fromarray(im_show)
        image_file_path = f'result_page_{pdf_test.split(".")[0]}_{idx + 1}.jpg'  # 为每页保存不同的图像文件
        im_show.save(image_file_path)

    print(f"处理完成，结果已保存到 {txt_file_path} 和图片文件。")
pdf_txt(pdf_folder_path,pdf_test)