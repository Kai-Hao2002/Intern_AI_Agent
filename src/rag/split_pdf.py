# rag/split_pdf.py
import os
import json
from pypdf import PdfReader, PdfWriter

def split_pdf_by_chapters(document_name, input_pdf, output_dir, chapter_ranges, file_prefix=""):
    """
    將大型 PDF 根據指定的頁碼範圍拆分成多個小檔案。
    Splits a large PDF into smaller files based on specified page ranges.
    """
    if not os.path.exists(input_pdf):
        print(f"❌ Input file not found: {input_pdf}")
        print(f"Please ensure that you have placed {document_name} in the correct path.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 建立輸出資料夾 (Created output directory): {output_dir}")

    print(f"📖 正在讀取 (Reading) {input_pdf} ... (檔案較大，請耐心等候幾秒鐘 / Large file, please wait)")
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    print(f"✅ 讀取完成 (Read complete)，總頁數 (Total pages): {total_pages}\n")

    for chapter_name, (start_page, end_page) in chapter_ranges.items():
        start_idx = max(0, start_page - 1)
        end_idx = min(total_pages, end_page)

        writer = PdfWriter()
        for i in range(start_idx, end_idx):
            writer.add_page(reader.pages[i])

        output_filename = os.path.join(output_dir, f"{file_prefix}{chapter_name}.pdf")
        with open(output_filename, "wb") as output_pdf:
            writer.write(output_pdf)

        print(f"✂️ 成功產出 (Successfully created): {output_filename} (Pages {start_page} to {end_page})")

if __name__ == "__main__":
    
    OUTPUT_FOLDER = "./docs/processed"
    
    # 尋找上一層目錄中的設定檔 (Find the config file in the parent directory)
    CONFIG_FILE_PATHS = [
        "docs_config.json",           # 如果在根目錄執行 (If executed from root)
        "../../docs_config.json"      # 如果在 src/rag/ 執行 (If executed from src/rag/)
    ]
    
    config_path = next((p for p in CONFIG_FILE_PATHS if os.path.exists(p)), None)
    
    if not config_path:
        print("❌ 找不到設定檔 'docs_config.json'。請確保該檔案存在於專案根目錄。")
        print("❌ Cannot find 'docs_config.json'. Please ensure it exists in the project root.")
        exit(1)
        
    print(f"📄 載入文件設定檔 (Loading document config from): {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        DOCUMENTS_TO_PROCESS = json.load(f)

    print("🚀 開始執行 PDF 拆分作業... (Starting PDF split process...)")
    
    for doc_key, config in DOCUMENTS_TO_PROCESS.items():
        print(f"\n[{doc_key}]")
        split_pdf_by_chapters(
            document_name=doc_key,
            input_pdf=config["path"],
            output_dir=OUTPUT_FOLDER,
            chapter_ranges=config["chapters"],
            file_prefix=config["prefix"]
        )

    print("\n🎉 所有指定章節拆分完成！請接著執行 ingest_data.py 來建立純淨的知識庫。")
    print("🎉 All specified chapters split successfully! Proceed to run ingest_data.py to build the clean knowledge base.")