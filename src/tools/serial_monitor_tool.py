# tools/serial_monitor_tool.py
import serial
import time
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BAUDRATE = int(os.getenv("TARGET_BAUDRATE", 115200))

def monitor_uart_log(port_name: str, duration: int = 5, max_retries: int = 3):
    """
    連接到指定的序列埠，持續監聽指定秒數的日誌。
    加入重試機制，防止因為暫時性的 USB 斷線導致腳本崩潰。
    Connect to the specified sequence port and continuously listen to the logs for a specified number of seconds.
    Add a retry mechanism to prevent the script from crashing due to temporary USB disconnection.
    """
    print(f"📡 Connecting to sequence port: {port_name}, preparing to listen for {duration} seconds...")
    
    captured_logs = []
    error_detected = False
    ser = None
    
    for attempt in range(1, max_retries + 1):
        try:
            ser = serial.Serial(port_name, DEFAULT_BAUDRATE, timeout=1)
            print(f"✅ Successfully opened serial port {port_name} (attempts: {attempt}/{max_retries})")
            break
        except serial.SerialException as e:
            if attempt == max_retries:
                return False, f"❌ 嚴重錯誤：無法開啟序列埠 {port_name}。已重試 {max_retries} 次皆失敗。錯誤細節：{e}\n🚨 [系統指令]: 請回報使用者檢查硬體連線或 USB 驅動。"
            
            print(f"⚠️ Unable to open sequence port, will try again in {2} seconds ({attempt}/{max_retries})...")
            time.sleep(2)

    if ser and ser.is_open:
        try:
            end_time = time.time() + duration
            while time.time() < end_time:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        captured_logs.append(line)
                        if "panic" in line.lower() or "hardfault" in line.lower() or "error" in line.lower():
                            error_detected = True
                            
        except serial.SerialException as e:
            return False, f"❌ 警告：在監聽過程中序列埠突然中斷連線！錯誤細節：{e}"
        finally:
            ser.close()

    if not captured_logs:
        return True, "✅ The listening session ended, and no UART output was received (the development board may not be powered on or may be in a timeout state)."

    log_summary = "\n".join(captured_logs)
    
    if error_detected:
        return False, f"❌ 警告！在 UART 日誌中偵測到系統崩潰或異常：\n{log_summary}"
    else:
        return True, f"✅ 系統運作正常，擷取到的日誌如下：\n{log_summary}"

if __name__ == "__main__":
    test_port = input("Please enter the virtual sequence port path (e.g., /dev/ttys001): ")
    success, report = monitor_uart_log(test_port, duration=8)
    print("\n" + "="*40)
    print(report)
    print("="*40)