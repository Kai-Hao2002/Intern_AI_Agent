import os
import pty
import time
import sys

def start_virtual_board():
    # 建立一對虛擬序列埠 (Master/Slave)
    master, slave = pty.openpty()
    slave_name = os.ttyname(slave)
    
    print("="*50)
    print("🔥 [Mock Board] i.MX93 虛擬開發板已準備就緒！")
    print(f"🔌 請將 AI Agent (pyserial) 連接到這個虛擬序列埠: {slave_name}")
    print("="*50)
    
    # 🛠️ 關鍵修改：讓程式暫停，等你設定好第二個終端機後再繼續
    input("\n👉 請在第二個終端機啟動監聽腳本後，回到這裡按 [Enter] 鍵模擬開發板上電開機...")
    
    # 模擬的開機日誌，故意安插一個 Kernel panic 錯誤
    logs = [
        "U-Boot 2023.04-imx_v2023.04_2.1.0+g0000000000 for NXP i.MX93 EVK\n",
        "Starting kernel ...\n",
        "Linux version 6.1.22-nxp (oe-user@oe-host) (aarch64-poky-linux-gcc)\n",
        "Machine model: NXP i.MX93 11X11 EVK board\n",
        "[    0.000000] cma: Reserved 320 MiB at 0x00000000\n",
        "[    2.145000] cfg80211: Loading compiled-in X.509 certificates\n",
        "[    3.012000] Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block(0,0)\n",
        "[    3.015000] CPU: 0 PID: 1 Comm: swapper/0 Not tainted 6.1.22-nxp\n",
        "[    3.020000] Hardware name: NXP i.MX93 11X11 EVK board (DT)\n",
        "[    3.025000] Call trace:\n",
        "[    3.028000]  dump_backtrace+0x98/0x120\n",
        "[    3.032000]  panic+0x168/0x334\n",
        "[    3.035000] ---[ end Kernel panic - not syncing: VFS: Unable to mount root fs ]---\n"
    ]

    print("\n[開發板開機中... 持續輸出 UART Log...]")
    try:
        for line in logs:
            os.write(master, line.encode('utf-8'))
            # 將 1 秒改為 0.1 秒，模擬真實 UART 噴 Log 的速度
            time.sleep(0.1) 
            
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[Mock Board] 電源關閉。")

if __name__ == "__main__":
    start_virtual_board()