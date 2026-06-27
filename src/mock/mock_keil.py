# src/mock/mock_keil.py
import sys
import os
import time

LOG_SUCCESS = """Build target 'Target 1'
compiling main.c...
linking...
Program Size: Code=1024 RO-data=256 RW-data=0 ZI-data=512  
".\\Objects\\my_project.axf" - 0 Error(s), 0 Warning(s).
"""

LOG_ERROR_UNSUPPORTED_PIN = """Build target 'Target 1'
compiling main.c...
target_workspace/mcu_firmware/main.c(15): error: #35: #error directive: "Platform limitation: 'kLPI2C_4PinUnidirectional' is physically NOT supported on i.MX93. Please check chip-specific LPI2C information."
".\\Objects\\my_project.axf" - 1 Error(s), 0 Warning(s).
"""

if __name__ == "__main__":
    print("[Mock Keil] UV4.exe emulator started...")
    time.sleep(1) # 模擬編譯耗時
    
    # 決定日誌輸出的路徑
    out_file = "build_log.txt"
    if "-o" in sys.argv:
        try:
            out_file = sys.argv[sys.argv.index("-o") + 1]
        except IndexError:
            pass

    # 精準定位 target_workspace 裡面的 main.c (考量 mock_keil.py 所在層級)
    target_c_file = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "target_workspace", "mcu_firmware", "main.c"
    ))
    
    outcome = LOG_SUCCESS
    
    # 檢查實體檔案並讀取內容
    if os.path.exists(target_c_file):
        with open(target_c_file, "r", encoding="utf-8") as f:
            content = f.read()
            # 💡 核心邏輯：只要檔案裡面還有 kLPI2C_4PinUnidirectional，編譯就會報錯
            if 'kLPI2C_4PinUnidirectional' in content:
                outcome = LOG_ERROR_UNSUPPORTED_PIN
    else:
        outcome = f"Fatal Error: Target file not found at {target_c_file}!"

    # 將結果寫入編譯日誌
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(outcome)

    print(f"[Mock Keil] Build finished. Log written to {out_file}")

    # 回傳給作業系統的 Exit Code (這會影響 run_keil_tool.py 的判斷)
    if "Error:" in outcome or "error:" in outcome.lower() or "Fatal" in outcome:
        sys.exit(2)
    else:
        sys.exit(0)