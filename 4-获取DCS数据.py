import serial
import time
import argparse
import logging
from datetime import datetime

def configure_logger():
    """配置日志记录"""
    logging.basicConfig(
        filename='modbus_monitor.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def calculate_crc(data):
    """计算MODBUS RTU CRC校验值"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

def parse_modbus_response(data):
    """解析MODBUS响应数据"""
    if len(data) < 5:  # 至少需要5字节
        return None, "数据长度不足"
    
    slave_addr = data[0]
    func_code = data[1]
    
    # 检查响应是否为异常响应
    if func_code & 0x80:
        error_code = data[2]
        error_msg = {
            0x01: "不支持的功能码",
            0x02: "不支持的数据地址",
            0x03: "不支持的数据值",
            0x04: "设备故障",
            0x05: "确认请求，需要更长时间处理",
            0x06: "设备忙",
        }.get(error_code, f"未知错误码: {error_code}")
        return None, f"异常响应 - 功能码: {func_code & 0x7F}, 错误: {error_code}"
    
    # 处理不同功能码
    if func_code == 3:  # 读保持寄存器
        byte_count = data[2]
        expected_length = 3 + byte_count + 2
        
        if len(data) != expected_length:
            return None, f"数据长度不匹配 - 预期: {expected_length}, 实际: {len(data)}"
        
        # 提取寄存器值
        registers = []
        for i in range(byte_count // 2):
            reg_value = (data[3 + i*2] << 8) | data[4 + i*2]
            registers.append(reg_value)
        
        return {
            'slave_addr': slave_addr,
            'func_code': func_code,
            'byte_count': byte_count,
            'registers': registers,
            'function': '读保持寄存器'
        }, None
    
    elif func_code == 10:  # 写多个保持寄存器
        if len(data) != 8:  # 写响应固定8字节
            return None, f"功能码10响应长度错误 - 预期: 8, 实际: {len(data)}"
        
        start_addr = (data[2] << 8) | data[3]
        reg_count = (data[4] << 8) | data[5]
        
        return {
            'slave_addr': slave_addr,
            'func_code': func_code,
            'start_addr': start_addr,
            'reg_count': reg_count,
            'function': '写多个保持寄存器'
        }, None
    
    else:
        return None, f"不支持的功能码: {func_code}"

def main():
    parser = argparse.ArgumentParser(description='MODBUS数据监控程序')
    parser.add_argument('-p', '--port', default='COM3', help='串口号 (默认: COM3)')
    parser.add_argument('-b', '--baudrate', type=int, default=9600, help='波特率 (默认: 9600)')
    parser.add_argument('-t', '--timeout', type=float, default=1.0, help='超时时间 (秒, 默认: 1.0)')
    args = parser.parse_args()
    
    logger = configure_logger()
    logger.info(f"程序启动，参数: {args}")
    
    try:
        ser = serial.Serial(
            port=args.port,
            baudrate=args.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=args.timeout
        )
        
        print(f"成功连接到 {ser.name} (波特率: {args.baudrate})")
        print("正在接收MODBUS数据... (按Ctrl+C停止)")
        print("-" * 70)
        
        buffer = bytearray()
        last_byte_time = time.time()
        
        while True:
            if ser.in_waiting > 0:
                new_data = ser.read(ser.in_waiting)
                buffer.extend(new_data)
                last_byte_time = time.time()
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # 显示原始数据
                hex_data = ' '.join([f"{byte:02X}" for byte in new_data])
                print(f"[{timestamp}] 收到数据: {hex_data}")
            
            # 检查是否有完整的MODBUS帧
            # MODBUS RTU帧之间至少有3.5个字符时间的间隔
            if buffer and (time.time() - last_byte_time) > 0.05:  # 假设3.5个字符时间约50ms
                # 尝试解析MODBUS帧
                while len(buffer) >= 5:
                    # 查找帧起始 (从站地址，范围1-247)
                    start_idx = 0
                    while start_idx < len(buffer) and (buffer[start_idx] < 1 or buffer[start_idx] > 247):
                        start_idx += 1
                    
                    if start_idx >= len(buffer) - 4:
                        break
                    
                    # 尝试解析帧
                    frame_data = buffer[start_idx:]
                    parsed_data, error = parse_modbus_response(frame_data)
                    
                    if parsed_data:
                        # 计算CRC校验
                        crc_calculated = calculate_crc(frame_data[:-2])
                        crc_received = (frame_data[-2] << 8) | frame_data[-1]
                        crc_valid = crc_calculated == crc_received
                        
                        # 成功解析一帧
                        frame_length = len(frame_data)
                        buffer = buffer[start_idx + frame_length:]
                        
                        # 显示解析结果
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] 解析MODBUS帧:")
                        print(f"       从站地址: {parsed_data['slave_addr']}")
                        print(f"       功能码: {parsed_data['func_code']} ({parsed_data['function']})")
                        
                        if parsed_data['func_code'] == 3:
                            # 读保持寄存器
                            registers = parsed_data['registers']
                            if len(registers) >= 12:
                                print("       保持寄存器值 (40001-40012):")
                                for i in range(12):
                                    print(f"         地址 400{(i+1):03d}: {registers[i]}")
                            else:
                                print(f"       保持寄存器值 ({len(registers)} 个):")
                                for i, val in enumerate(registers):
                                    print(f"         地址 400{(i+1):03d}: {val}")
                        
                        elif parsed_data['func_code'] == 10:
                            # 写多个保持寄存器
                            start_addr = parsed_data['start_addr']
                            reg_count = parsed_data['reg_count']
                            print(f"       起始地址: {start_addr} (400{(start_addr+1):03d})")
                            print(f"       寄存器数量: {reg_count}")
                        
                        print(f"       CRC校验: {'有效' if crc_valid else '无效'}")
                        print("-" * 70)
                        logger.info(f"解析成功 - 数据: {parsed_data}")
                    
                    else:
                        # 无法解析，可能数据不完整
                        break
            
            time.sleep(0.01)
            
    except serial.SerialException as e:
        print(f"串口错误: {e}")
        logger.error(f"串口错误: {e}")
    except KeyboardInterrupt:
        print("\n程序已停止")
        logger.info("程序手动停止")
    except Exception as e:
        print(f"未知错误: {e}")
        logger.error(f"未知错误: {e}", exc_info=True)
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口已关闭")
            logger.info("串口已关闭")

if __name__ == "__main__":
    main()