# src/tools/patch_tool.py
import os
import re
import difflib
from langchain_core.tools import tool

@tool
def apply_patch_tool(file_path: str, search_text: str, replace_text: str) -> str:
    """
    【程式碼修復工具】當你發現編譯錯誤，需要修改 C 語言或 Device Tree 原始碼時，呼叫此工具。
    請精確提供檔案路徑、要被替換的「完整原始程式碼片段」，以及「修正後的新程式碼片段」。
    此工具會自動產生標準的 .patch 檔案並套用修改。
    [Code Repair Tool] Use this tool when you find compilation errors and need to modify C language or Device Tree source code.
    Please provide the exact file path, the complete source code snippet to be replaced, and the corrected source code snippet.
    This tool will automatically generate a standard .patch file and apply the modifications.
    """
    print(f"\n🛠️ [Patch Tool] is attempting to repair the file: {file_path}")
    

    if not os.path.exists(file_path):
        return (f"❌ Repair failed: file `{file_path}` not found on local machine.\n"
                f"🚨 [System command]: Please do not attempt to repair this file using patch_tool again! Please explain to the user in text how to modify it.")
    # 2. Read the original file content
    with open(file_path, "r", encoding="utf-8") as f:
        original_code = f.read()

    # 策略一：精確比對 (Exact Match) - 最安全且快速
    if search_text in original_code:
        new_code = original_code.replace(search_text, replace_text)
        match_strategy = "精確比對 (Exact Match)"
    else:
        # 策略二：模糊比對 (Fuzzy Match) - 忽略縮排、連續空白與換行差異
        # 將 search_text 去除頭尾空白，並將內部所有連續空白替換為 \s+
        escaped_search = re.escape(search_text.strip())
        flexible_search = re.sub(r'(\\\s)+', r'\s+', escaped_search)
        
        # 在原始碼中尋找所有符合的片段
        matches = list(re.finditer(flexible_search, original_code))
        
        if len(matches) == 1:
            # 找到唯一匹配，進行座標替換
            start, end = matches[0].span()
            new_code = original_code[:start] + replace_text + original_code[end:]
            match_strategy = "模糊比對 (Whitespace Insensitive)"
        elif len(matches) > 1:
            return (f"❌ Repair failed: `search_text` found a matching block at {len(matches)} in the file.\n"
                    f"🚨 [System Command]: Please provide a longer and more unique context (including several lines of error-free code before and after) to ensure the uniqueness of the replacement.")
        else:
            return (f"❌ Repair failed: The specified `search_text` could not be found in `{file_path}`.\n"
                    f"🚨 [System Command]: The code you provided may differ significantly from the original file. Please carefully compare the line numbers in the error log with the source code. If multiple failures occur, please stop using the tool and directly output your suggested modifications.")

    # 使用 difflib 產生標準的 Unified Diff (Git 格式)
    diff = difflib.unified_diff(
        original_code.splitlines(keepends=True),
        new_code.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=3 
    )
    patch_content = "".join(diff)

    # 如果沒有產生差異，代表 AI 企圖替換成一模一樣的內容
    if not patch_content:
        return "⚠️ Repair failed: `replace_text` contains exactly the same content as the original file; the code has not changed."

    # 儲存 .patch 檔案
    patch_dir = os.path.join(os.path.dirname(__file__), "..", "..", "patches")
    os.makedirs(patch_dir, exist_ok=True)
    
    base_name = os.path.basename(file_path).replace(".", "_")
    patch_filename = os.path.join(patch_dir, f"fix_{base_name}_auto.patch")
    
    with open(patch_filename, "w", encoding="utf-8") as f:
        f.write(patch_content)

    # 實際將修改寫回原檔案
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)

    return (f"✅ Repair successful! Modifications have been applied to `{file_path}` (match strategy: {match_strategy}).\n"
            f"📦 The system has automatically generated a standard patch file: `{patch_filename}`.\n"
            f"Please report this to the Supervisor node immediately and request DevOps_Expert to recompile.")