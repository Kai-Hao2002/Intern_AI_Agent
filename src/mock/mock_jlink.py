import time
import sys

print("SEGGER J-Link Commander V7.60b (Compiled...)")
print("Connecting to J-Link via USB...")
time.sleep(1)
print("Device MIMX9352_M33 selected.")
print("Connecting to target via SWD")
time.sleep(1)

# 檢查是否有傳入腳本參數
if "-CommanderScript" in sys.argv:
    print(f"Executing script: {sys.argv[sys.argv.index('-CommanderScript') + 1]}")

print("Downloading file [./Objects/M33_Firmware.hex]...")
time.sleep(2) # 模擬燒錄寫入時間

# 印出關鍵字讓主腳本的 grep 可以抓到成功判定
print("O.K.")
print("Verify successful.")
print("Verified OK")

sys.exit(0)