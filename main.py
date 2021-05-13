import cv2
from cv2 import *
import numpy as np
import serial
import threading
from datetime import datetime
import schedule
import time
import number

# prevTime = 0
number = number.number()

cam_triger = True

# 아두이노
PORT = 'COM9'  # 아두이노 포트번호
BaudRate = 9600
global cnt
cnt = 0

ARD = serial.Serial(PORT, BaudRate)  # 시리얼 통신 변수 생성

send_alarm = "HIGH"  # 사운드 센서로 보내기 위한 HIGH값
send_alarm = send_alarm.encode("utf-8")  # 통신위해 문자열 캐스팅

# YOLO load
net = cv2.dnn.readNet("./yolo/yolov3_final.weights", "./yolo/yolov3.cfg")
classes = []
with open("./yolo/obj.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
colors = np.random.uniform(0, 255, size=(len(classes), 3))

# webcam
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

def Ardread():  # 아두이노로 부터 값 읽어 오기 위한 함수
    if ARD.readable():  # 아두이노로부터 값 읽어오기
        LINE = ARD.readline()  # 줄마다 읽기
        output = int(LINE)
        if cnt == 0:
            print(output)
        return output # 정수형으로 전달
    else:
        print("읽기 실패 from _Ardread_")

def nextFrameSlot():
    global cnt
    prevTime = 0.0

    while True:
        # if cam_triger is True:
            ret, frame = cap.read()  # 다음 프레임 읽기
            if ret:
                frame = cv2.flip(frame, 1)

                # Detecting objects
                blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
                net.setInput(blob)
                outs = net.forward(output_layers)

                # 정보를 화면에 표시
                class_ids = []
                confidences = []
                boxes = []
                for out in outs:
                    for detection in out:
                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]

                        # 신뢰도가 50%가 넘어가야지만 감지
                        if confidence > 0.5:
                            print(confidence)

                            # Object detected
                            center_x = int(detection[0] * 800)
                            center_y = int(detection[1] * 600)
                            w = int(detection[2] * 800)
                            h = int(detection[3] * 600)
                            # 좌표
                            x = int(center_x - w / 2)
                            # if x < 0:
                            #     x = 0
                            # elif x > frame.shape[1]:
                            #     x = frame.shape[1]
                            y = int(center_y - h / 2)
                            # if y < 0:
                            #     y = 0
                            # elif y > frame.shape[0]:
                            #     y = frame.shape[0]

                            boxes.append([x, y, w, h])
                            confidences.append(float(confidence))
                            class_ids.append(class_id)

                indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

                # 시간이 5초이상 지났으면서 인식률이 50% 이하이면 종료
                if len(boxes) ==0:
                    if prevTime == 0.0:
                        prevTime = time.time()

                    else:
                        _timer = time.time() - prevTime
                        if _timer >= 8.0:
                            ARD.write(send_alarm)
                            cnt = 1
                            pic()
                            number.main()
                            cap.release()
                            cv2.destroyAllWindows()
                            break
                else:
                    prevTime = 0.0

                font = cv2.FONT_HERSHEY_PLAIN
                for i in range(len(boxes)):
                    if i in indexes:
                        x, y, w, h = boxes[i]
                        label = str(classes[class_ids[i]])
                        try:
                            color = colors[i]
                        except Exception as ex:
                            print(ex)
                        #cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(frame, label, (x, y + 30), font, 3, color, 3)

                cv2.imshow("disabled_camera", frame)
                if cv2.waitKey(1) != -1:  # 1ms 동안 키 입력 대기 ---②
                    cap.release()
                    cv2.destroyAllWindows()
                    break  # 아무 키라도 입력이 있으면 중지

            else:
                print("no cam")

def pic():
    cap2 = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    ret, img = cap2.read()
    cv2.imwrite("./images/car_number.jpg", img)
    print("지금")
    cap2.release()
    cv2.destroyAllWindows()


frame_th = threading.Thread(target=nextFrameSlot)

while True:
        if Ardread() < 50:
            if cam_triger is True:
                frame_th.start()
                cam_triger = False
            elif cnt >= 1:
                cnt+=1
                if cnt == 30:
                    ARD.write(1)

# cap.release()  # 자원 반납
# cv2.destroyAllWindows()