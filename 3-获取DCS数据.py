import serial
import time
import argparse
import logging
from datetime import datetime

def configure_logger():
    """配置日志记录"""
    logging.basicConfig(
        filename='serial_monitor.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def main():
    # 配置命令行参数
    parser = argparse.ArgumentParser(description='串口数据监控程序')
    parser.add_argument('-p', '--port', default='COM3', help='串口号 (默认: COM3)')
    parser.add_argument('-b', '--baudrate', type=int, default=9600, help='波特率 (默认: 9600)')
    parser.add_argument('-t', '--timeout', type=float, default=1.0, help='超时时间 (秒, 默认: 1.0)')
    args = parser.parse_args()
    
    logger = configure_logger()
    logger.info(f"程序启动，参数: {args}")
    
    try:
        # 配置串口参数
        ser = serial.Serial(
            port=args.port,
            baudrate=args.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=args.timeout
        )
        
        print(f"成功连接到 {ser.name} (波特率: {args.baudrate})")
        print("正在接收数据... (按Ctrl+C停止)")
        print("-" * 50)
        
        while True:
            # 检查是否有数据可读
            if ser.in_waiting > 0:
                # 读取数据
                data = ser.read(ser.in_waiting)
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # 计算数据长度
                data_length = len(data)
                
                try:
                    # 尝试以ASCII格式解码
                    ascii_data = data.decode('ascii', errors='replace').strip()
                    ascii_display = ascii_data if ascii_data else "(无ASCII数据)"
                except:
                    ascii_display = "(无法解码为ASCII)"
                
                # 转换为十六进制字符串
                hex_data = ' '.join([f"{byte:02X}" for byte in data])
                hex_display = hex_data if hex_data else "(无数据)"
                
                # 显示数据
                print(f"[{timestamp}] 长度: {data_length} 字节")
                print(f"       ASCII: {ascii_display}")
                print(f"       HEX:   {hex_display}")
                print("-" * 50)
                
                # 记录到日志
                logger.info(f"收到数据 - 长度: {data_length} 字节, HEX: {hex_display}")
            
            # 短暂休眠避免CPU占用过高
            time.sleep(0.01)
            
    except serial.SerialException as e:
        print(f"串口错误: {e}")
        logger.error(f"串口错误: {e}")
        print("\n提示:")
        print("  1. 请确认串口设备已正确连接")
        print("  2. 确认串口未被其他程序占用")
        print("  3. 检查串口参数设置是否正确")
    except KeyboardInterrupt:
        print("\n程序已停止")
        logger.info("程序手动停止")
    except Exception as e:
        print(f"未知错误: {e}")
        logger.error(f"未知错误: {e}", exc_info=True)
    finally:
        # 确保串口被关闭
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口已关闭")
            logger.info("串口已关闭")

if __name__ == "__main__":
    main()