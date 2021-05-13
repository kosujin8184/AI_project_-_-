import json
import cv2
import requests
import sys
import pymysql
from datetime import datetime


class number():
    def __init__(self):
        self.LIMIT_PX = 1024
        self.LIMIT_BYTE = 1024*1024  # 1MB
        self.LIMIT_BOX = 40
        self.APPKEY = 'd9538dd5b3e7d5bc2ede85b56e30bfc8'
        self.IMGPATH = './images/car_number.jpg'

    def kakao_ocr_resize(self, image_path: str):
        """
        ocr detect/recognize api helper
        ocr api의 제약사항이 넘어서는 이미지는 요청 이전에 전처리가 필요.

        pixel 제약사항 초과: resize
        용량 제약사항 초과  : 다른 포맷으로 압축, 이미지 분할 등의 처리 필요. (예제에서 제공하지 않음)

        :param image_path: 이미지파일 경로
        :return:
        """
        image = cv2.imread(image_path)
        height, width, _ = image.shape

        if self.LIMIT_PX < height or self.LIMIT_PX < width:
            ratio = float(self.LIMIT_PX) / max(height, width)
            image = cv2.resize(image, None, fx=ratio, fy=ratio)
            height, width, _ = height, width, _ = image.shape

            # api 사용전에 이미지가 resize된 경우, recognize시 resize된 결과를 사용해야함.
            image_path = "{}_resized.jpg".format(image_path)
            cv2.imwrite(image_path, image)

            return image_path
        return None

    def kakao_ocr(self, image_path: str, appkey: str):
        """
        OCR api request example
        :param image_path: 이미지파일 경로
        :param appkey: 카카오 앱 REST API 키
        """
        API_URL = 'https://dapi.kakao.com/v2/vision/text/ocr'

        headers = {'Authorization': 'KakaoAK {}'.format(appkey)}

        image = cv2.imread(image_path)
        jpeg_image = cv2.imencode(".jpg", image)[1]
        data = jpeg_image.tobytes()

        return requests.post(API_URL, headers=headers, files={"image": data})

    def dbconn(self):
        mydb = pymysql.connect(
            user="root",
            passwd="holymoly1!",
            host="10.1.4.103",
            db="bad_guys"
            #charset="utf-8"
        )
        print("dbconn success!!")

        return mydb

    def main(self):
        # mysql db 연결
        mydb = self.dbconn()
        # db 조작에 필요한 커서 선언
        cursor = mydb.cursor(pymysql.cursors.DictCursor)

        def select():
            cursor.execute("select * from number_plate")
            result = cursor.fetchall()
            for row in result:
                print(row)

        # if len(sys.argv) != 3:
        #     print("Please run with args: $ python example.py /path/to/image appkey")
        image_path, appkey = self.IMGPATH, self.APPKEY

        resize_impath = self.kakao_ocr_resize(image_path)
        if resize_impath is not None:
            image_path = resize_impath
            print("원본 대신 리사이즈된 이미지를 사용합니다.")

        output = self.kakao_ocr(image_path, appkey).json()

        # print("[OCR] output:\n{}\n".format(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2)))

        # 번호판을 가져오는 부분
        number_plate = ""

        def toString(string):
            string = str(string).replace("[", "")
            string = str(string).replace("]", "")
            string = str(string).replace("'", "")
            print(string)
            return str(string)

        num = 0
        for obj in output['result']:
            if num != 0:
                number_plate += " " + toString(obj['recognition_words'])
            else:
                number_plate += toString(obj['recognition_words'])
            num += 1

        print(number_plate)

        if len(number_plate) > 0:
            date = datetime.today().strftime("%Y-%m-%d")
            time = datetime.today().strftime("%H:%M:%S")
            # print(date)
            # print(time)
            sql = "insert into number_plate(recog_date, recog_time, number_plate) values(%s, %s, %s);"
            val = (date, time, number_plate)
            cursor.execute(sql, val)
            mydb.commit()

            select()





# if __name__ == "__main__":
#     main()