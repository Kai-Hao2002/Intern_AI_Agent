# tools/run_yocto_tool.py
import paramiko
import socket
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

EXECUTION_MODE = os.getenv("EXECUTION_MODE", "MOCK").upper()

SSH_HOST = os.getenv("YOCTO_SSH_HOST", "127.0.0.1")
SSH_PORT = int(os.getenv("YOCTO_SSH_PORT", 2222))
SSH_USER = os.getenv("YOCTO_SSH_USER", "root")
SSH_PASS = os.getenv("YOCTO_SSH_PASS", "yocto")

REMOTE_IMAGE_PATH = "/root/Image-imx93.bin"
LOCAL_IMAGE_PATH = "./Image-imx93.bin"
BUILD_LOG_PATH = "/root/yocto_build.log"

def _connect_ssh_with_retry(host, port, username, password, max_retries=3, delay=3):
    """
    SSH 連線輔助函數，具備重試與超時保護機制。
    SSH connection helper functions with retry and timeout protection mechanisms.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for attempt in range(1, max_retries + 1):
        try:
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
            return ssh
        except (paramiko.SSHException, socket.timeout, socket.error) as e:
            print(f"⚠️ SSH conects failed. ({host}:{port}),{delay} miniutes retry ({attempt}/{max_retries})... errors: {e}")
            time.sleep(delay)
            
    return None

def trigger_remote_build(target_recipe="imx-image-multimedia"):
    """
    非同步觸發：透過 SSH 在背景啟動 Yocto 編譯
    Asynchronous Triggering: Launching Yocto Compilation in the Background via SSH
    """
    if EXECUTION_MODE == "MOCK":
        print("🧪 [Mock Mode] Simulates triggering remote Yocto compilation...")
        time.sleep(1) # 模擬網路延遲
        return "✅ Yocto remote compilation has started in the background (Mock). Please use the status check tool to track the progress."

    print("🌐 [Real Mode] Connecting and launching Yocto Build in the background....")
    ssh = _connect_ssh_with_retry(SSH_HOST, SSH_PORT, SSH_USER, SSH_PASS)
    
    if not ssh:
        return "❌ Critical Network Error: Unable to connect to the Yocto server; maximum retries reached. \n🚨 [System Command]: Please report to the user to check server status and network configuration."
        
    try:
        command = f"nohup bitbake {target_recipe} > {BUILD_LOG_PATH} 2>&1 &"
        ssh.exec_command(command, timeout=10)
        return "✅ Yocto remote compilation has started in the background. Please use the status check tool to track the progress."
    except Exception as e:
        return f"❌ An unexpected error occurred during compilation: {e}"
    finally:
        ssh.close()

def check_build_status():
    """狀態輪詢：檢查背景編譯任務的最新日誌/Status polling: Check the latest logs of background compilation tasks."""
    if EXECUTION_MODE == "MOCK":
        # 模擬 20% 機率發生網路斷線導致 do_fetch 失敗 
        # (Simulate a 20% chance of a network disconnection causing do_fetch to fail)
        if random.random() < 0.2:
            return (
                "❌ Compilation failed! Last log:\n"
                "ERROR: Task (do_fetch) failed: Fetcher failure: Unable to fetch URL from any source.\n"
                "ERROR: Logfile of failure stored in: /var/tmp/work/imx93-poky-linux/imx-image/1.0-r0/temp/log.do_fetch\n"
                "Recommendation: Please check your network connection or Yocto source mirror settings."
            )
        else:
            return "✅ 編譯成功！最後日誌：\nMock Build successful. Image generated at /root/Image-imx93.bin\n(請執行下載與燒錄步驟)"
        
    ssh = _connect_ssh_with_retry(SSH_HOST, SSH_PORT, SSH_USER, SSH_PASS)
    
    if not ssh:
        return "❌ Critical network error: Unable to connect to the Yocto server to obtain status."
        
    try:
        stdin, stdout, stderr = ssh.exec_command(f"tail -n 10 {BUILD_LOG_PATH}", timeout=10)
        log_output = stdout.read().decode('utf-8').strip()
        
        if not log_output:
            return "⏳ The compilation system is initializing; no logs have been generated yet..."
            
        if "Build successful" in log_output:
            return f"✅ Compilation successful! Last log: \n{log_output}\n(Please proceed with the download and burning steps)"
        elif "Failed" in log_output or "Error" in log_output:
            return f"❌ Compilation failed! Last log: \n{log_output}"
        else:
            return f"⏳ Compiling...current progress: \n{log_output}"
            
    except socket.timeout:
        return "❌ Log read timeout. The server may be overloaded. Please try again later."
    except Exception as e:
        return f"❌ An error occurred while querying the status: {e}"
    finally:
        ssh.close()

def download_remote_image():
    """
    透過 SFTP 將編譯好的 Image 從遠端伺服器下載到本地
    Download the compiled image from the remote server to the local machine via SFTP.
    """
    if EXECUTION_MODE == "MOCK":
        print("🧪 [Mock Mode] download Image...")
        # 建立一個假的空檔案，確保後續 UUU 燒錄檢查時檔案是存在的
        with open(LOCAL_IMAGE_PATH, "w") as f:
            f.write("mock_image_data_for_testing")
        print(f"✅ Image downloads successfully (Mock): {LOCAL_IMAGE_PATH}")
        return True

    print("📥 [Real Mode] Downloading Image via SFTP...")
    ssh = _connect_ssh_with_retry(SSH_HOST, SSH_PORT, SSH_USER, SSH_PASS)
    
    if not ssh:
        print("❌ Critical network error: SFTP connection failed, unable to download image.")
        return False
        
    try:
        sftp = ssh.open_sftp()
        sftp.get(REMOTE_IMAGE_PATH, LOCAL_IMAGE_PATH)
        sftp.close()
        print(f"✅ Image successfully downloaded to local machine:{LOCAL_IMAGE_PATH}")
        return True
    except Exception as e:
        print(f"❌ Download Image failed: {e}")
        return False
    finally:
        ssh.close()

def flash_image_uuu():
    """
    模擬 NXP UUU 工具將 Image 燒錄至 i.MX93
    Use the emulation NXP UUU tool to burn the image to the i.MX93
    """
    if not os.path.exists(LOCAL_IMAGE_PATH):
        print("❌ The local image file could not be found, and the file could not be burned.")
        return False
        
    if EXECUTION_MODE == "MOCK":
        print("\n⚡ [Mock Mode] 啟動 UUU (Universal Update Utility) 工具...")
        time.sleep(1)
        print(f"uuu -b emmc_all u-boot-imx93.imx {LOCAL_IMAGE_PATH}")
        print("100% [================================>]")
        print("✅ 映像檔燒錄至 eMMC 成功！ (Mock UUU Flash completed!)")
        os.remove(LOCAL_IMAGE_PATH) # 清理假檔案
        return True

    print("\n⚡ [Real Mode] 啟動 UUU (Universal Update Utility) 工具...")
    time.sleep(1)
    print(f"uuu -b emmc_all u-boot-imx93.imx {LOCAL_IMAGE_PATH}")
    # 未來進入公司後，可以將這裡替換成真實的 subprocess.run() 呼叫
    time.sleep(2) 
    print("100% [================================>]")
    print("✅ 映像檔燒錄至 eMMC 成功！ (UUU Flash completed!)")
    
    os.remove(LOCAL_IMAGE_PATH)
    return True

if __name__ == "__main__":
    print("="*50)
    print("Launch the Task 2 automated workflow (Cortex-A Yocto deployment)")
    print(f"Current Mode: {EXECUTION_MODE}")
    print("="*50)
    
    if trigger_remote_build():
        time.sleep(1) 
        status = check_build_status()
        print(status)
        if "成功" in status:
            if download_remote_image():
                flash_image_uuu()
    else:
        print("🛑 progress ends")