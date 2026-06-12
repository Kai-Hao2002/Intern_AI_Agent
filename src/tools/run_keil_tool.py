import os
import subprocess
import re
import sys # 新增引入 sys 以取得當前 python 執行環境

# ==========================================
# ⚙️ 路徑與環境設定 (Mock 測試模式 - Mac/Linux 友善版)
# ==========================================
PYTHON_EXEC = sys.executable 

# 取得目前 run_keil_tool.py 所在的資料夾路徑 (即 src/tools)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 往上一層找到 src，再進入 mock 資料夾
KEIL_UV4_PATH = os.path.join(CURRENT_DIR, "../mock/mock_keil.py")
JLINK_PATH = os.path.join(CURRENT_DIR, "../mock/mock_jlink.py")

print(f"🔍 [Debug] Keil Path resolves to: {KEIL_UV4_PATH}")
print(f"🔍 [Debug] Does Keil mock exist? {os.path.exists(KEIL_UV4_PATH)}")

PROJECT_PATH = "mock_project.uvprojx" 
BUILD_LOG = "build_log.txt"
JLINK_SCRIPT = "flash_m33.jlink"

def parse_build_log(log_path):
    """
    解析 Keil 編譯日誌，過濾出 Error 與 Warning。
    這將是未來回傳給 Claude 分析的重要反饋 (Feedback Loop)。
    """
    if not os.path.exists(log_path):
        return "❌ 找不到編譯日誌檔案 (Build log not found).", False

    errors = []
    warnings = []
    
    # 建立正則表達式來捕捉 Keil MDK 典型的錯誤與警告格式
    error_pattern = re.compile(r'.*(error|Error|ERROR).*')
    warning_pattern = re.compile(r'.*(warning|Warning|WARNING).*')

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines:
                clean_line = line.strip()
                
                # 🛠️ 修正重點：排除 Keil 最後一行的編譯總結，避免 "0 Error(s)" 被當成錯誤
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
    """執行 Keil 命令列進行編譯"""
    print(f"🚀 開始編譯專案: {PROJECT_PATH} ...")
    
    # Keil UV4 CLI 指令: -b (build), -j0 (隱藏 GUI), -o (輸出 log)
    # 注意：Keil 的 -o 參數產出的 log 預設會放在專案檔 (.uvprojx) 所在的同一層目錄
    #cmd = [KEIL_UV4_PATH, "-b", PROJECT_PATH, "-j0", "-o", BUILD_LOG]
    cmd = [PYTHON_EXEC, KEIL_UV4_PATH, "-b", PROJECT_PATH, "-j0", "-o", BUILD_LOG]
    
    # 使用 subprocess 執行，並等待其完成
    process = subprocess.run(cmd, capture_output=True, text=True)
    
    # Keil UV4 的 Exit Codes:
    # 0 = No Errors or Warnings, 1 = Warnings only, 2 = Errors, 3 = Fatal Errors, 11 = Cannot open project
    exit_code = process.returncode
    log_file_path = os.path.join(os.path.dirname(PROJECT_PATH), BUILD_LOG)
    
    if exit_code in [0, 1, 2]:
        print("🔍 正在解析編譯結果...")
        report, is_success = parse_build_log(log_file_path)
        # 🛠️ 修改這裡：同時回傳成功狀態與報告字串，讓 AI 能讀取
        return is_success, report 
    else:
        return False, f"❌ 嚴重錯誤！Keil 無法開啟或編譯失敗 (Exit Code: {exit_code})"

def flash_target():
    """執行 J-Link 命令列進行自動燒錄"""
    print("⚡ 開始透過 J-Link 燒錄 Cortex-M33...")
    
    # 呼叫 JLink.exe 並傳入腳本
    #cmd = [JLINK_PATH, "-CommanderScript", JLINK_SCRIPT]
    cmd = [PYTHON_EXEC, JLINK_PATH, "-CommanderScript", JLINK_SCRIPT]
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    
    # 檢查 J-Link 輸出是否包含成功的關鍵字 (例如 O.K. 或 Verify successful)
    if "O.K." in process.stdout or "Verified OK" in process.stdout:
        print("✅ 燒錄成功！ (Flash completed successfully!)")
        return True
    else:
        print("❌ 燒錄失敗！ (Flash failed!)")
        print("--- J-Link Output ---")
        # 如果失敗，印出最後 10 行 Log 方便除錯
        print("\n".join(process.stdout.split('\n')[-10:]))
        return False

if __name__ == "__main__":
    # 🛠️ 正確解包 Tuple 回傳值
    is_success, report_str = build_project()
    
    # 印出解析後的報告
    print(report_str)
    
    if is_success:
        flash_target()
    else:
        print("🛑 編譯失敗，停止燒錄流程。")