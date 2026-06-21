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
        return (f"❌ Repair failed: file `{file_path}` not found on local machine.\n"
                f"🚨 [System command]: Please do not attempt to repair this file using patch_tool again! Please explain to the user in text how to modify it.")
    # 2. Read the original file content
    with open(file_path, "r", encoding="utf-8") as f:
        original_code = f.read()

    # 3. Verify whether search_text actually exists in the code.
    if search_text not in original_code:
        return (f"❌ Repair failed: The specified `search_text` could not be found in {file_path}.\n"
                f"🚨 [System Command]: Ensure the fragments are completely identical. If it fails multiple times, stop calling the tool and print out the suggested modifications directly.")

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

    return (f"✅ Fixed successfully! Modifications have been applied to `{file_path}`.\n"
            f"📦 BSP standard patch file automatically generated: `{patch_filename}`.\n"
            f"Please report to the supervisor node immediately and request DevOps_Expert to recompile.")