# src/agent/agent_tools.py
import time
from langchain_core.tools import tool
from tools.run_keil_tool import build_project, flash_target
from tools.run_yocto_tool import trigger_remote_build, check_build_status, flash_image_uuu, download_remote_image
from tools.serial_monitor_tool import monitor_uart_log

@tool
def compile_and_flash_mcu(dummy_arg: str = "") -> str:
    """
    用於編譯並燒錄 Cortex-M33 (MCU) 的 Keil 專案。
    Keil project for compiling and programming Cortex-M33 (MCU).
    """
    is_success, build_report = build_project()
    if is_success:
        flash_target()
        return f"MCU compiles and programs sucessfully! \nlog:\n{build_report}"
    else:
        return f"MCU compiles failed. Errors:\n{build_report}"

@tool
def start_mpu_build(dummy_arg: str = "") -> str:
    """
    用於觸發遠端 Yocto 伺服器進行 Cortex-A55 (MPU) 的映像檔編譯。
    Used to trigger the compilation of the Cortex-A55 (MPU) image file on a remote Yocto server.
    """
    return trigger_remote_build()

@tool
def check_mpu_build_status(dummy_arg: str = "") -> str:
    """
    用於檢查 Yocto 編譯進度。如果回報「進行中」，請等待並重新呼叫。
    Used to check the Yocto compilation progress. If it returns "In Progress", please wait and call again.
    """
    time.sleep(2)
    return check_build_status()

@tool
def deploy_mpu_image(dummy_arg: str = "") -> str:
    """
    當 Yocto 編譯成功後，呼叫此工具下載 Image 並透過 UUU 燒錄。
    Once Yocto has compiled successfully, call this tool to download the image and flash it via UUU.
    """
    dl_success = download_remote_image()
    if not dl_success:
        return "❌ download the image failed!"
    flash_success = flash_image_uuu()
    return "✅ UUU flashes successfully!" if flash_success else "❌ UUU flashes failed!"

@tool
def monitor_device_logs(port_name: str) -> str:
    """
    用於監聽實體或虛擬開發板的 UART 序列埠開機日誌。
    Used to monitor the boot logs of the UART serial port on a physical or virtual development board.
    """
    success, report = monitor_uart_log(port_name, duration=8)
    return report