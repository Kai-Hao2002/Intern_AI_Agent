# tools/patch_toolpy
import os
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
        return (f"❌ 修復失敗：在本地端找不到檔案 `{file_path}`。\n"
                f"🚨 [系統指令]: 請不要再嘗試使用 patch_tool 修復此檔案！請直接用文字向使用者說明需要如何修改。")
    
    # 2. Read the original file content
    with open(file_path, "r", encoding="utf-8") as f:
        original_code = f.read()

    # 3. Verify whether search_text actually exists in the code.
    if search_text not in original_code:
        return (f"❌ 修復失敗：在 {file_path} 中找不到指定的 `search_text`。\n"
                f"🚨 [系統指令]: 請確保片段完全一致。如果多次失敗，請停止呼叫工具，直接印出建議修改方案。")

    # 4. Perform code replacement
    new_code = original_code.replace(search_text, replace_text)

    # 5. Use difflib to generate a standard Unified Diff (fully compatible with Git Patch)
    diff = difflib.unified_diff(
        original_code.splitlines(keepends=True),
        new_code.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=3 
    )
    patch_content = "".join(diff)

    # 6. save to .patch file
    patch_dir = os.path.join(os.path.dirname(__file__), "..", "..", "patches")
    os.makedirs(patch_dir, exist_ok=True)
    
    # Use the file name as part of the patch name.
    base_name = os.path.basename(file_path).replace(".", "_")
    patch_filename = os.path.join(patch_dir, f"fix_{base_name}_auto.patch")
    
    with open(patch_filename, "w", encoding="utf-8") as f:
        f.write(patch_content)

    # 7. The changes are actually written to the original file (using a patch).
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)

    return (f"✅ 成功修復！已將修改套用至 `{file_path}`。\n"
            f"📦 已自動生成 BSP 標準補丁檔案：`{patch_filename}`。\n"
            f"請立即回報主管節點，並請求 DevOps_Expert 重新進行編譯。")