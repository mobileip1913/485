from flask import Flask, render_template
import time
import serial
import struct
import threading
import logging
import os

app = Flask(__name__)

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_temperature_and_humidity():
    try:
        ser = serial.Serial('COM3', 9600, timeout=1)
        logging.info("成功打开串口 COM3")
        command = bytearray([0x01, 0x03, 0x00, 0x00, 0x00, 0x02, 0xC4, 0x0B])
        ser.write(command)
        logging.info("已发送读取温湿度数据的命令")
        response = ser.read(9)
        logging.info("从串口读取到的数据长度为 %s，数据内容为 %s", len(response), response)
        if len(response) == 9:
            if response[0] == 0x01 and response[1] == 0x03:
                temperature = struct.unpack('>h', bytes([response[3], response[4]]))[0] / 100
                humidity = struct.unpack('>h', bytes([response[5], response[6]]))[0] / 100
                return temperature, humidity
            else:
                logging.warning("响应数据格式错误")
                return None, None
        else:
            logging.warning("未收到完整响应数据")
            return None, None
    except Exception as e:
        logging.error("出现异常: %s", e)
        return None, None
    finally:
        if 'ser' in locals():
            ser.close()
            logging.info("已关闭串口")

def update_data():
    global temperature, humidity
    while True:
        temp, hum = get_temperature_and_humidity()
        if temp is not None and hum is not None:
            temperature = temp
            humidity = hum
        time.sleep(1)

temperature = None
humidity = None

thread = threading.Thread(target=update_data)
thread.start()

@app.route('/')
def index():
    return render_template('index.html', temperature=temperature, humidity=humidity)

if __name__ == '__main__':
    app.run(debug=True, port=8080)