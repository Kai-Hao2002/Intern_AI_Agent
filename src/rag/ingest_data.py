# rag/ingest_data.py
import os
import shutil
import pickle
import pdfplumber
from langchain_core.documents import Document
from langchain_community.document_loaders import PDFPlumberLoader, TextLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


DOC_PATH = "./docs/processed"
DB_PATH = "./chroma_db"

# ==========================================
# 🌐 網頁資源設定區 (Web Resources)
# ==========================================
WEB_URLS = [
    "https://www.keil.com/support/man/docs/uv4cl/uv4cl_commandline.htm", # Keil MDK CLI
    "https://kb.segger.com/J-Link_Commander",                            # J-Link Commander
    "https://github.com/nxp-imx/mfgtools/blob/master/README.md"          # NXP UUU (Universal Update Utility)
]


def parse_pdf_with_markdown_tables(file_path):
    """
    讀取 PDF，並將提取到的表格強制轉換為 Markdown 格式附加在頁面文字後，
    以保持暫存器與記憶體位址的 2D 對應結構。
    
    Reads a PDF and forces extracted tables into Markdown format appended to the page text,
    preserving the 2D structural relationship of registers and memory addresses.
    """
    docs = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # 提取該頁的純文字 / Extract plain text of the page
            content = page.extract_text() or ""
            
            # 提取該頁的表格 / Extract tables from the page
            tables = page.extract_tables()
            
            for table in tables:
                if not table: continue
                
                # 將整個表格內容轉為小寫字串，用來判斷表格類型
                # Convert the entire table to a lowercase string to determine its type
                table_text_lower = str(table).lower()
                
                # 智慧注入 (Smart Injection): 
                if "start address" in table_text_lower or "start" in table_text_lower and "end" in table_text_lower:
                    # 如果表格有 Start/End Address，這才是真正的記憶體映射表！
                    # If it has Start/End Address, this is the REAL Memory Map!
                    md_table = "\n\n### [CRITICAL: Memory Map, Base Address, Start Address]\n"
                elif "offset" in table_text_lower or "register" in table_text_lower:
                    # 如果只有 offset，這只是普通的暫存器表
                    # If it only has offset, it's just a regular register table
                    md_table = "\n\n### [Hardware Register Map, Offset]\n"
                else:
                    md_table = "\n\n### [Extracted Table]\n"
                
                for row_idx, row in enumerate(table):
                    clean_row = [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
                    md_table += "| " + " | ".join(clean_row) + " |\n"
                    
                    if row_idx == 0:
                        md_table += "|" + "|".join(["---" for _ in clean_row]) + "|\n"
                
                # 將 Markdown 表格附加到該頁的內容中 / Append Markdown table to the page content
                content += md_table + "\n"
            
            # 封裝為 LangChain 認識的 Document 格式 / Wrap into LangChain Document format
            docs.append(Document(
                page_content=content,
                metadata={"source": os.path.basename(file_path), "page": i + 1}
            ))
    return docs

def build_vector_database():
    """讀取 PDF 與網頁內容，建立/覆蓋本地向量資料庫與 BM25 索引"""
    
    # 1. 清除舊資料庫 (Clear old DB)
    if os.path.exists(DB_PATH):
        print(f"🗑️ Clearing old vector database at {DB_PATH}...")
        shutil.rmtree(DB_PATH)

    docs = []

    # 2. 讀取本地 PDF 文件 (Load Local PDFs)
    if os.path.exists(DOC_PATH):
        print("📄 Loading local documents...")
        for filename in os.listdir(DOC_PATH):
            file_path = os.path.join(DOC_PATH, filename)
            
            # If it's PDF, using PDFPlumberLoader
            if filename.lower().endswith(".pdf"):
                print(f"   📖 Reading PDF: {filename}")
                parsed_docs = parse_pdf_with_markdown_tables(file_path)
                docs.extend(parsed_docs)
                
            # If it's Markdown or TXT, using TextLoader
            elif filename.lower().endswith(".md") or filename.lower().endswith(".txt"):
                print(f"   📝 Reading Text/Markdown: {filename}")
                loader = TextLoader(file_path, encoding='utf-8')
                docs.extend(loader.load())
                
            # Skip unknow format
            else:
                print(f"   ⏩ Skipping unsupported file: {filename}")
    else:
        print(f"⚠️ Warning: Folder {DOC_PATH} not found.")

    # 3. 讀取線上網頁文件 (Load Web Documents)
    if WEB_URLS:
        print("\n🌐 Loading Web documents via WebBaseLoader...")
        try:
            # WebBaseLoader Supports direct URL List inputs
            web_loader = WebBaseLoader(WEB_URLS)
            web_docs = web_loader.load()
            
            # Merge webpage content with PDF content
            docs.extend(web_docs)
            print(f"   ✅ Successfully loaded {len(WEB_URLS)} web pages.")
        except Exception as e:
            print(f"   ❌ Error loading web pages: {e}")
            print("   💡 Note: Please confirm that you have executed `pip install beautifulsoup4`.")

    # Check if any data has been captured.
    if not docs:
        print("\n⚠️ No documents found from either PDFs or Web. Exiting.")
        return
        
    print(f"\n✅ Total document chunks/pages loaded: {len(docs)}")

    # 4. 文本切塊 (Text Chunking)
    # The chunking here will apply to both the plain text parsed from PDF and HTML.
    print("✂️ Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3500, chunk_overlap=500)
    splits = text_splitter.split_documents(docs)

    # 5. 建立與儲存資料庫 (Embedding and Storing)
    print("🧠 Creating embeddings and saving to ChromaDB...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=DB_PATH)
    
    # 6. 將 splits 存成 pickle 檔案供 BM25 讀取 (Save for Ensemble Retriever)
    print("📦 Saving documents for BM25 Keyword Search...")
    with open("splits.pkl", "wb") as f:
        pickle.dump(splits, f)
        
    print("\n🎉 Vector database & BM25 index built successfully! (PDF + Web)")

if __name__ == "__main__":
    build_vector_database()