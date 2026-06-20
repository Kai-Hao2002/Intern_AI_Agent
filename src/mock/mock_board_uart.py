import os
import pty
import time
import sys
import random

def get_random_scenario():
    """隨機決定這次開機要發生什麼狀況 (Randomly decide what happens during this boot)"""
    scenarios = [
        "NORMAL_PANIC",    # 傳統的 Kernel Panic
        "BAUDRATE_ERROR",  # 亂碼 (Baud rate 設錯)
        "TIMEOUT",         # 開機沒反應 (卡死)
        "HARD_FAULT"       # Cortex-M33 崩潰
    ]
    # 增加 NORMAL_PANIC 的機率方便你平時測試 (Increase NORMAL_PANIC probability for normal testing)
    return random.choices(scenarios, weights=[40, 20, 20, 20])[0]

def start_virtual_board():
    master, slave = pty.openpty()
    slave_name = os.ttyname(slave)
    
    scenario = get_random_scenario()
    
    print("="*50)
    print("🔥 [Mock Board] i.MX93 虛擬開發板已準備就緒！")
    print(f"🔌 請將 AI Agent (pyserial) 連接到這個虛擬序列埠: {slave_name}")
    print(f"🎲 本次隨機模擬情境 (Current Scenario): {scenario}")
    print("="*50)
    
    input("\n👉 請在第二個終端機啟動監聽腳本後，回到這裡按 [Enter] 鍵模擬開發板上電開機...")
    print("\n[開發板開機中... 持續輸出 UART Log...]")

    try:
        if scenario == "TIMEOUT":
            # 模擬硬體死機，什麼都不吐 (Simulate hardware freeze, outputting nothing)
            time.sleep(10)
            
        elif scenario == "BAUDRATE_ERROR":
            # 模擬 Baud rate 不匹配時的亂碼 (Simulate gibberish when baud rate mismatches)
            gibberish = "$%&*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
            for _ in range(20):
                random_chars = "".join(random.choices(gibberish, k=50)) + "\n"
                os.write(master, random_chars.encode('utf-8'))
                time.sleep(0.1)

        elif scenario == "HARD_FAULT":
            # 模擬 MCU M33 核心的 HardFault (Simulate HardFault on the MCU M33 core)
            logs = [
                "Cortex-M33 Booting...\n",
                "Initializing LPI2C2...\n",
                "*** HARD FAULT ***\n",
                "CFSR: 0x00000082 (PRECISERR)\n",
                "BFAR: 0x44350000 (Invalid Memory Access)\n",
                "System Halted.\n"
            ]
            for line in logs:
                os.write(master, line.encode('utf-8'))
                time.sleep(0.2)

        else: # NORMAL_PANIC
            logs = [
                "U-Boot 2023.04-imx_v2023.04_2.1.0+g0000000000 for NXP i.MX93 EVK\n",
                "Starting kernel ...\n",
                "Linux version 6.1.22-nxp (oe-user@oe-host) (aarch64-poky-linux-gcc)\n",
                "[    3.012000] Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block(0,0)\n",
                "[    3.035000] ---[ end Kernel panic - not syncing: VFS: Unable to mount root fs ]---\n"
            ]
            for line in logs:
                os.write(master, line.encode('utf-8'))
                time.sleep(0.2)
            
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[Mock Board] 電源關閉。")

if __name__ == "__main__":
    start_virtual_board()