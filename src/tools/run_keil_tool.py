# tools/run_keil_tool.py
import os
import subprocess
import re
import sys
import logging

logger = logging.getLogger(__name__)
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# ⚙️ Enviroment Setting
# ==========================================
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "MOCK").upper()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXEC = sys.executable

# 1. Dynamically configure execution path and instruction prefix
if EXECUTION_MODE == "REAL":
    print("🔥 [System] 啟動真實硬體模式 (REAL MODE)")
    # Read the actual path from environment variables; if not found, use the default common installation path.
    KEIL_UV4_PATH = os.getenv("KEIL_REAL_PATH", r"C:\Keil_v5\UV4\UV4.exe")
    JLINK_PATH = os.getenv("JLINK_REAL_PATH", r"C:\Program Files\SEGGER\JLink\JLink.exe")
    
    CMD_PREFIX_KEIL = [KEIL_UV4_PATH]
    CMD_PREFIX_JLINK = [JLINK_PATH]
else:
    print("🧪 [System] 啟動模擬測試模式 (MOCK MODE)")
    KEIL_UV4_PATH = os.path.join(CURRENT_DIR, "../mock/mock_keil.py")
    JLINK_PATH = os.path.join(CURRENT_DIR, "../mock/mock_jlink.py")
    
    CMD_PREFIX_KEIL = [PYTHON_EXEC, KEIL_UV4_PATH]
    CMD_PREFIX_JLINK = [PYTHON_EXEC, JLINK_PATH]


PROJECT_PATH = "mock_project.uvprojx" 
BUILD_LOG = "build_log.txt"
JLINK_SCRIPT = "flash_m33.jlink"

def parse_build_log(log_path):
    """
    解析 Keil 編譯日誌，過濾出 Error 與 Warning。
    這將是未來回傳給 Claude 分析的重要反饋 (Feedback Loop)。
    Analyze the Keil build logs and filter out Errors and Warnings.
    This will be crucial feedback sent back to Claude for future analysis (Feedback Loop).
    """
    if not os.path.exists(log_path):
        return "❌ 找不到編譯日誌檔案 (Build log not found).", False

    errors = []
    warnings = []

    error_pattern = re.compile(r'.*(error|Error|ERROR).*')
    warning_pattern = re.compile(r'.*(warning|Warning|WARNING).*')

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines:
                clean_line = line.strip()
                
                if "Error(s)" in clean_line and "Warning(s)" in clean_line:
                    continue
                
                if error_pattern.search(clean_line):
                    errors.append(clean_line)
                elif warning_pattern.search(clean_line):
                    warnings.append(clean_line)
    except Exception as e:
        return f"讀取日誌時發生錯誤: {e}", False

    # 組合精簡報告給 AI (或終端機)
    report_lines = []
    if errors:
        report_lines.append("❌ [編譯錯誤 Errors Found]:")
        report_lines.extend(errors)
    
    if warnings:
        report_lines.append("⚠️ [編譯警告 Warnings Found]:")
        report_lines.extend(warnings)
        
    if not errors and not warnings:
        report_lines.append("✅ [編譯完美通過 Build Passed: 0 Errors, 0 Warnings]")

    build_success = len(errors) == 0
    return "\n".join(report_lines), build_success

def build_project():
    """執行 Keil 命令列進行編譯/Compile using the Keil command line."""
    logger.info(f"Start compiling the MCU project: {PROJECT_PATH} ...")
    
    cmd = [PYTHON_EXEC, KEIL_UV4_PATH, "-b", PROJECT_PATH, "-j0", "-o", BUILD_LOG]
    process = subprocess.run(cmd, capture_output=True, text=True)
    exit_code = process.returncode
    
    if exit_code in [0, 1, 2]:
        logger.info("Parsing compilation result logs...")
        report, is_success = parse_build_log(os.path.join(os.path.dirname(PROJECT_PATH), BUILD_LOG))
        return is_success, report 
    else:
        logger.error(f"Critical error! Keil cannot be opened or compilation failed.(Exit Code: {exit_code})")
        return False, f"❌ Critical error! Keil cannot be opened or compilation failed. (Exit Code: {exit_code})"

def flash_target():
    """執行 J-Link 命令列進行自動燒錄/ Execute J-Link command line for automatic flashing"""
    logger.info("Starting J-Link flashing Cortex-M33...")
    
    cmd = [PYTHON_EXEC, JLINK_PATH, "-CommanderScript", JLINK_SCRIPT]
    process = subprocess.run(cmd, capture_output=True, text=True)
    
    if "O.K." in process.stdout or "Verified OK" in process.stdout:
        logger.info("✅ MCU 燒錄成功！ (Flash completed successfully!)")
        return True
    else:
        logger.error("❌ MCU 燒錄失敗！(Flash Failed)")
        logger.debug(f"J-Link Output:\n{process.stdout}")
        return False

if __name__ == "__main__":
    is_success, report_str = build_project()
    
    print(report_str)
    
    if is_success:
        flash_target()
    else:
        print("🛑 Compilation failed, burning process stopped.")