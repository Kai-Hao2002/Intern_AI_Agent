import paramiko
import os
import time

# ==========================================
# ⚙️ 遠端伺服器與本地環境設定 (Mock 測試模式)
# ==========================================
# 指向你的 Docker 容器
SSH_HOST = "127.0.0.1"
SSH_PORT = 2222
SSH_USER = "root"
SSH_PASS = "yocto"

REMOTE_IMAGE_PATH = "/root/Image-imx93.bin"
LOCAL_IMAGE_PATH = "./Image-imx93.bin"

def remote_build_yocto():
    """透過 SSH 連線到遠端伺服器並執行 bitbake"""
    print("🌐 正在連線到 Yocto Build Server...")
    
    ssh = paramiko.SSHClient()
    # 自動接受未知的 SSH 密鑰 (測試環境適用)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS)
        print("✅ SSH 連線成功！")
        
        print("🚀 觸發遠端編譯: bitbake imx-image-multimedia...")
        # 執行我們寫在 Dockerfile 裡的假 bitbake
        stdin, stdout, stderr = ssh.exec_command("bitbake imx-image-multimedia")
        
        # 即時印出遠端伺服器的終端機輸出
        for line in iter(stdout.readline, ""):
            print(f"[Remote] {line.strip()}")
            
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("\n📥 編譯完成，開始透過 SFTP 下載 Image...")
            sftp = ssh.open_sftp()
            sftp.get(REMOTE_IMAGE_PATH, LOCAL_IMAGE_PATH)
            sftp.close()
            print(f"✅ Image 成功下載至本地端: {LOCAL_IMAGE_PATH}")
            build_success = True
        else:
            print("❌ 遠端編譯失敗！")
            build_success = False
            
    except Exception as e:
        print(f"❌ SSH 作業發生錯誤: {e}")
        build_success = False
    finally:
        ssh.close()
        
    return build_success

def flash_image_uuu():
    """模擬 NXP UUU 工具將 Image 燒錄至 i.MX93"""
    if not os.path.exists(LOCAL_IMAGE_PATH):
        print("❌ 找不到本地 Image 檔案，無法燒錄。")
        return False
        
    print("\n⚡ 啟動 UUU (Universal Update Utility) 工具...")
    time.sleep(1)
    print(f"uuu -b emmc_all u-boot-imx93.imx {LOCAL_IMAGE_PATH}")
    time.sleep(2) # 模擬燒錄時間
    
    print("100% [================================>]")
    print("✅ 映像檔燒錄至 eMMC 成功！ (UUU Flash completed!)")
    
    # 測試完畢後把假檔案刪除保持環境乾淨
    os.remove(LOCAL_IMAGE_PATH)
    return True

if __name__ == "__main__":
    print("="*50)
    print("啟動 Task 2 自動化工作流 (Cortex-A Yocto 部署)")
    print("="*50)
    
    if remote_build_yocto():
        flash_image_uuu()
    else:
        print("🛑 流程終止。")