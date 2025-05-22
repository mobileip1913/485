import serial
from flask import Flask, render_template_string
from pymodbus.server import StartSerialServer  # 3.x版本正确导入
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
import threading
import asyncio
import signal
import time

# 配置参数
SERIAL_PORT = 'COM3'
BAUDRATE = 9600
STOPBITS = serial.STOPBITS_ONE
SLAVE_IDS = [1, 2, 3, 4]

# 机组数据定义（确保使用列表[]）
UNIT_METRICS = {
    1: [
        "#1机发电机有功功率", "#1机发电机无功功率", "#1机汽机主蒸汽温度",
        "#1机主蒸汽电动门前压力", "#1机再热器蒸汽温度", "脱硫岛氮氧化物到DCS",
        "脱硫岛粉尘DUST到DCS", "#1机凝汽器真空", "#1机工业抽气总流量",
        "脱硫岛二氧化硫到DCS", "#1机民用供热流量"
    ],
    2: [
        "#2机发电机有功功率", "#2机发电机无功功率", "#2机汽机主蒸汽温度",
        "#2机主蒸汽电动门前压力", "#2机再热器蒸汽温度", "脱硫岛氮氧化物到DCS",
        "脱硫岛粉尘DUST到DCS", "#2机凝汽器真空", "#2机工业抽气总流量",
        "脱硫岛二氧化硫到DCS", "#2机民用供热流量"
    ],
    3: [
        "#3机发电机有功功率", "#3机发电机无功功率", "#3机汽机主蒸汽温度",
        "#3机主蒸汽电动门前压力", "#3机再热器蒸汽温度", "脱硫岛氮氧化物到DCS",
        "脱硫岛粉尘DUST到DCS", "#3机凝汽器真空", "#3机工业抽气总流量",
        "脱硫岛二氧化硫到DCS", "#3机民用供热流量"
    ],
    4: [
        "#4机发电机有功功率", "#4机发电机无功功率", "#4机汽机主蒸汽温度",
        "#4机主蒸汽电动门前压力", "#4机再热器蒸汽温度", "脱硫岛氮氧化物到DCS",
        "脱硫岛粉尘DUST到DCS", "#4机凝汽器真空", "#4机工业抽气总流量",
        "脱硫岛二氧化硫到DCS", "#4机民用供热流量"
    ]
}


class DCSModbusSlave:
    def __init__(self):
        # 初始化数据存储
        self.datastore = {}
        for slave_id in SLAVE_IDS:
            hr_block = ModbusSequentialDataBlock(
                address=1,  # 寄存器起始地址（4001对应地址1）
                values=[0] * len(UNIT_METRICS[slave_id])  # 初始值全为0
            )
            slave_context = ModbusSlaveContext(hr=hr_block)
            self.datastore[slave_id] = slave_context

        self.context = ModbusServerContext(slaves=self.datastore, single=False)

        # 设备标识
        self.identity = ModbusDeviceIdentification(
            info_name={
                'VendorName': 'DCSMonitor',
                'ProductCode': 'DCS01',
                'VendorUrl': 'https://example.com',
                'ProductName': '机组数据从机',
                'ModelName': 'Modbus RTU Slave',
                'MajorMinorRevision': '1.0'
            }
        )

        # 异步服务器和事件循环
        self.server = None
        self.loop = None
        self.server_thread = None

        # 修复：初始化数据缓存（之前未定义）
        self.data_cache = {
            slave_id: {name: 0 for name in UNIT_METRICS[slave_id]}
            for slave_id in SLAVE_IDS
        }

    async def _start_server(self):
        """异步启动服务器的协程"""
        self.server = await StartSerialServer(
            context=self.context,
            identity=self.identity,
            port=SERIAL_PORT,
            baudrate=BAUDRATE,
            stopbits=STOPBITS,
            method='rtu',
            timeout=2
        )
        print(f"Modbus RTU从机已启动，端口：{SERIAL_PORT}，从机地址：{SLAVE_IDS}")

    def start(self):
        """在单独线程中启动异步服务器"""

        def run_async_server():
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # 设置Windows事件循环策略（关键修复）
            if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            # 运行服务器协程
            try:
                self.loop.run_until_complete(self._start_server())
                self.loop.run_forever()
            except Exception as e:
                print(f"服务器错误: {e}")
            finally:
                # 确保资源正确关闭
                if self.server:
                    self.server.close()
                self.loop.close()

        # 启动服务器线程
        self.server_thread = threading.Thread(target=run_async_server, daemon=True)
        self.server_thread.start()

    def update_register(self, slave_id, index, value):
        """更新指定从机的寄存器值"""
        if slave_id in self.datastore and 0 <= index < len(UNIT_METRICS[slave_id]):
            # 获取对应从机的保持寄存器数据块
            hr_block = self.datastore[slave_id].hr
            # 更新单个寄存器值
            hr_block.setValues(1 + index, [value])
            # 更新缓存
            metric_name = UNIT_METRICS[slave_id][index]
            self.data_cache[slave_id][metric_name] = value

    def stop(self):
        """优雅地停止服务器"""
        if self.server and self.server.is_running():
            self.server.shutdown()
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop())


# Web服务部分
app = Flask(__name__)
slave = DCSModbusSlave()


@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DCS Modbus从机数据</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .status-card { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .metric-value { transition: color 0.3s; }
            .metric-value:hover { color: #3b82f6; }
        </style>
    </head>
    <body class="bg-gray-50 p-4">
        <h1 class="text-2xl font-bold text-gray-900 mb-6 text-center">DCS Modbus从机实时数据</h1>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {% for slave_id in slave.data_cache|sort %}
            <div class="bg-white rounded-lg p-6 status-card">
                <h2 class="text-xl font-semibold text-green-600 mb-4">#{{ slave_id }}机从机</h2>
                <div class="space-y-2">
                    {% for name, value in slave.data_cache[slave_id].items() %}
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-gray-600">{{ name }}</span>
                        <span class="text-lg font-mono metric-value">{{ value }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        <div class="text-center mt-6 text-sm text-gray-500">
            提示：可通过Modbus主站（如Modbus Poll）读取地址4001-4012获取数据
        </div>
    </body>
    </html>
    ''', slave=slave)


# 添加信号处理，确保程序可以优雅退出
def handle_exit(signum, frame):
    print("接收到退出指令，正在关闭服务器...")
    slave.stop()
    exit(0)


if __name__ == "__main__":
    # 注册信号处理
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # 启动Modbus服务器
    slave.start()


    # 启动模拟数据更新线程
    def mock_data_updater():
        while True:
            for slave_id in SLAVE_IDS:
                for i in range(len(UNIT_METRICS[slave_id])):
                    # 生成更真实的模拟数据（带随机波动）
                    base_value = 100 + slave_id * 10 + i
                    value = base_value + int((time.time() % 10) - 5)  # 小范围波动
                    slave.update_register(slave_id, i, value)
            time.sleep(1)  # 每秒更新一次


    threading.Thread(target=mock_data_updater, daemon=True).start()

    # 启动Web服务
    print("启动Web服务，访问 http://localhost:5000 查看数据")
    app.run(host='0.0.0.0', port=5000, debug=True)