#main.py
import os
import sys
import logging
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

os.makedirs("logs", exist_ok=True)
log_file_path = os.path.join("logs", "agent_system.log")

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)                    
    ]
)

logger = logging.getLogger("Main")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

load_dotenv()

from src.agent.ai_agent import mas_app

def print_banner():
    """印出系統啟動橫幅/print banner"""
    print("=" * 65)
    print("🚀 NXP i.MX93 Embedded DevOps Multi-Agent System (MAS)")
    print(f"⚙️  執行模式 (Execution Mode): {os.getenv('EXECUTION_MODE', 'MOCK')}")
    print(f"📊 LangSmith 追蹤 (Tracking): {os.getenv('LANGCHAIN_TRACING_V2', 'false')}")
    print("=" * 65)
    print("可接受指令類型 (Supported Commands):")
    print("  1. MCU 編譯與燒錄 (MCU compile and flash")
    print("  2. MPU 遠端 Yocto 建置 (MPU remote Yocto build)")
    print("  3. 序列埠即時監聽與除錯 (Real-time monitoring and debugging of serial ports")
    print("  4. 視覺電路圖分析與測試計畫生成 (Visual circuit diagram analysis and test plan generation)")
    print("=" * 65)

def main():
    print_banner()
    logger.info("The embedded DevOps agent system has been launched.")
    
    TEST_MODE = "PROPOSED_MAS" # Change to "B1", "B2", "B3" 或 "PROPOSED_MAS"
    
    while True:
        try:
            user_text = input("\n👤 Enter the hardware error log or command (exit): ")
            if user_text.lower() in ['exit', 'quit']:
                logger.info("The system is shutting down safely...")
                break
                
            if not user_text.strip():
                continue
                
            logger.info(f"Receive user text {user_text}")
            
            initial_state = {
                "messages": [HumanMessage(content=user_text)],
                "mode": TEST_MODE,
                "retry_count": 0
            }

            for output in mas_app.stream(initial_state, {"recursion_limit": 20}):
                for node_name, state_update in output.items():
                    logger.info(f"--- 🔄 [Node] {node_name} executes finished ---")
                    if "messages" in state_update and state_update["messages"]:
                        print(f"\n🤖 {node_name} reports:\n{state_update['messages'][-1].content}\n")
                        
        except KeyboardInterrupt:
            logger.warning("Upon receiving the interrupt signal (KeyboardInterrupt), the system safely exits.")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred during system runtime:{e}", exc_info=True)

if __name__ == "__main__":
    main()