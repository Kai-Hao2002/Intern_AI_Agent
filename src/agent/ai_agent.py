import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from dotenv import load_dotenv

# 引入向量資料庫相關套件
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 引入前幾週寫好的自動化腳本
from tools.run_keil_tool import build_project, flash_target
from tools.run_yocto_tool import remote_build_yocto, flash_image_uuu
from tools.serial_monitor_tool import monitor_uart_log

# ==========================================
# 🧠 初始化 RAG 檢索器 
# ==========================================
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../chroma_db'))
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

if os.path.exists(DB_PATH):
    vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
else:
    print(f"⚠️ 找不到向量資料庫 {DB_PATH}，請先執行 ingest_data.py！")
    retriever = None

# ==========================================
# 🛠️ 註冊 AI 工具箱 (Agent Tools)
# ==========================================

@tool
def query_nxp_knowledge_base(query: str) -> str:
    """
    Search the NXP i.MX93 official knowledge base...
    
    【搜尋技巧提示】
    - 查詢記憶體位址時，請使用精簡的關鍵字，如："LPI2C2 memory map" 或 "LPI2C2 base address"。
    - 查詢系統崩潰原因時，請提取核心錯誤，如："Kernel panic Unable to mount root fs"。
    - 避免使用過長或包含太多動詞的句子作為 Query。
    """
    if not retriever:
        return "錯誤：NXP 知識庫未正確載入，無法查詢。"
    
    print(f"🔍 [AI 正在翻閱手冊 / AI is searching manual]: '{query}' ...")
    docs = retriever.invoke(query)
    
    context_list = []
    for i, doc in enumerate(docs, 1):
        source = os.path.basename(doc.metadata.get('source', 'Unknown'))
        context_list.append(f"--- Document Snippet {i} (Source: {source}) ---\n{doc.page_content}")
        
    return "\n\n".join(context_list)

@tool
def compile_and_flash_mcu():
    """用於編譯並燒錄 Cortex-M33 (MCU) 的 Keil 專案。"""
    is_success, build_report = build_project()
    if is_success:
        flash_target()
        return f"編譯與燒錄皆成功！\n日誌：\n{build_report}"
    else:
        return f"編譯失敗，未進行燒錄。請分析以下錯誤，並可主動使用知識庫查詢：\n{build_report}"

@tool
def compile_and_deploy_mpu():
    """
    用於透過 SSH 觸發遠端 Yocto 伺服器進行 Cortex-A55 (MPU) 的映像檔編譯與燒錄。
    """
    is_success = remote_build_yocto()
    if is_success:
        flash_image_uuu()
        # 🛠️ 魔法在這裡：我們在成功回傳值中，強烈暗示 Agent 進行下一步！
        return "Yocto 遠端編譯與下載燒錄成功！開發板準備重啟。請務必立刻呼叫 `monitor_device_logs` 工具來監聽開機狀態。"
    else:
        return "Yocto 遠端編譯或連線失敗，請檢查伺服器狀態。"

@tool
def monitor_device_logs(port_name: str) -> str:
    """
    用於監聽實體或虛擬開發板的 UART 序列埠開機日誌 (Boot Logs)。
    必須傳入序列埠名稱 (例如 '/dev/ttys001') 作為參數。
    如果回傳的日誌中包含系統崩潰 (Crash / Kernel panic)，請立刻提取錯誤關鍵字並呼叫 RAG 知識庫尋找原因。
    """
    success, report = monitor_uart_log(port_name, duration=8)
    return report

# ==========================================
# 👁️ 圖片處理輔助函數 (新增)
# ==========================================
def encode_image(image_path):
    """將本地圖片轉換為 Base64 字串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# ==========================================
# 🚀 啟動 Agent 大腦 / Start Agent Core
# ==========================================
def run_agent_loop():
    load_dotenv()
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError("❌ Missing GEMINI_API_KEY in .env file!")
    
    # 1. 載入模型 (Load Model)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_key, temperature=0)

    # 將全新的監聽工具註冊進去
    tools = [compile_and_flash_mcu, compile_and_deploy_mpu, monitor_device_logs, query_nxp_knowledge_base]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一位精通 NXP i.MX93 的硬體與韌體 AI 專家。"
                   "你現在具備視覺能力，可以讀取使用者上傳的電路圖(Schematics)。"
                   "當使用者要求為某個周邊(例如 I2C1)產生 Test Plan 時，你必須："
                   "1. 觀察圖片，找出該周邊對應的接腳 (Pinout)。"
                   "2. 主動呼叫 `query_nxp_knowledge_base` 查閱這些接腳在 i.MX93 暫存器中的基底位址或設定方式。"
                   "3. 綜合圖片資訊與手冊知識，生成一段專業的 C 或 Python 測試腳本與硬體設定指南。"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor

if __name__ == "__main__":
    agent = run_agent_loop()
    
    print("🤖 終極硬體 AI Agent 啟動完成！ (RAG 大腦 + 自動編譯 + 序列埠監聽已打通)")
    
    while True:
        # 🛠️ 改寫輸入邏輯：支援分離輸入文字與圖片
        user_text = input("\n👤 你的指令 (輸入 exit 離開): ")
        if user_text.lower() in ['exit', 'quit']:
            break
            
        img_path = input("🖼️ 要附上圖片嗎？(請貼上路徑，或直接按 Enter 跳過): ").strip()
        
        print("\n🧠 Agent 思考中...\n" + "-"*40)
        
        if img_path and os.path.exists(img_path):
            # 如果有圖片，將文字與圖片打包成 LangChain 支援的多模態格式
            base64_image = encode_image(img_path)
            multimodal_input = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]
            response = agent.invoke({"input": multimodal_input})
        else:
            # 如果沒圖片，就照舊傳送純文字
            if img_path: print("⚠️ 找不到圖片路徑，將僅傳送文字。")
            response = agent.invoke({"input": user_text})
            
        print("-"*40)
        print(f"\n🤖 Agent: {response['output']}")