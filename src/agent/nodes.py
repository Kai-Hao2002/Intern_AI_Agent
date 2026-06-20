# src/agent/nodes.py
import os
import re
import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent

# 引入本模組的依賴
from agent.state import AgentState, RouteDecision
from agent.utils import get_llm, get_image_base64
from agent.test_plan_schema import TestPlanSchema
from agent.agent_tools import (
    compile_and_flash_mcu, start_mpu_build, check_mpu_build_status, 
    deploy_mpu_image, monitor_device_logs
)
# 引入 RAG 與 Patch 工具
from tools.rag_tool import query_nxp_knowledge_base 
from tools.patch_tool import apply_patch_tool

logger = logging.getLogger(__name__)

# 初始化全域 LLM 與 Agent
llm = get_llm(provider="gemini")
knowledge_agent = create_react_agent(llm, tools=[query_nxp_knowledge_base, apply_patch_tool])
devops_agent = create_react_agent(llm, tools=[compile_and_flash_mcu, start_mpu_build, check_mpu_build_status, deploy_mpu_image])
qa_agent = create_react_agent(llm, tools=[monitor_device_logs])
zeroshot_agent = create_react_agent(llm, tools=[]) 

def generate_structured_test_plan(hardware_context: str, user_request: str) -> TestPlanSchema:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位精通 NXP i.MX93 的資深嵌入式 QA 自動化工程師。
        請根據提供的手冊上下文（Context），為指定的硬體周邊生成完整的自動化測試計畫。
        
        🚨 【Pytest 框架強制規範】(CRITICAL RULES):
        1. 測試腳本必須完全符合 `pytest` 框架的標準。
        2. 所有驗證函式必須以 `test_` 開頭。
        3. 請依賴 Python 原生的 `assert` 語句進行斷言。
        4. 絕對不要包含 `if __name__ == "__main__":` 區塊，也不要呼叫 `sys.exit()`。
        5. 腳本中須包含模擬或真實的暫存器讀寫函式 (如 `mem_read_32`)。
        
        硬體手冊上下文 / Hardware Manual Context:
        {context}
        """),
        ("human", "{input}")
    ])
    structured_llm = llm.with_structured_output(TestPlanSchema)
    chain = prompt | structured_llm
    return chain.invoke({"context": hardware_context, "input": user_request})

def supervisor_node(state: AgentState):
    current_mode = state.get("mode", "PROPOSED_MAS")
    if current_mode == "B1":
        return {"next_node": "ZeroShot_Expert"}
        
    system_prompt = f"""你是一位嵌入式系統專案主管。目前運行模式：[{current_mode}]。
        請遵循以下決策邏輯：
        1. 若需編譯與部署 -> 指派 DevOps_Expert
        2. 若需監聽序列埠，【或是要求分析電路圖與生成測試計畫 (Test Plan)】 -> 指派 QA_Expert
        3. 若遇見錯誤 (編譯錯誤或 Kernel Panic) -> 指派 Knowledge_Expert 查閱手冊並產生 Patch 修復。
        4. 🚨【反饋迴圈】：如果 Knowledge_Expert 回報「成功修復」，必須再次指派 DevOps_Expert 進行編譯驗證。
        5. 🛑【人工介入】：如果 Knowledge_Expert 要求人類介入，你必須立刻選擇 FINISH 結束任務。
        6. 只有當最終日誌顯示一切正常，且不需要人工介入時，才選擇 FINISH。
        """
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    router_llm = llm.with_structured_output(RouteDecision)
    decision = router_llm.invoke(messages)
    return {"next_node": decision.next_node}

def zeroshot_node(state: AgentState):
    sys_msg = SystemMessage(content="你是一位常規的嵌入式工程師。請僅依賴預訓練知識回答，不允許呼叫任何工具。請直接給出程式碼修復建議。")
    inputs = [sys_msg] + state["messages"]
    result = zeroshot_agent.invoke({"messages": inputs})
    return {"messages": result["messages"][len(inputs):], "next_node": "FINISH"}

def knowledge_node(state: AgentState):
    sys_msg = SystemMessage(content="""你是一位 NXP 系統專家。
    1. 使用 query_nxp_knowledge_base 檢索手冊。
    2. 若需修復，必須呼叫 `apply_patch_tool` 修改原始碼。
    3. 如果工具回報「找不到檔案」，絕對不要反覆嘗試，請改為直接在對話中輸出建議。
    """)
    baton = HumanMessage(content="[系統] 請查閱手冊庫，分析當前硬體配置或崩潰日誌。若需修復程式碼請嘗試使用工具，工具失敗則直接輸出建議。")
    inputs = [sys_msg] + state["messages"] + [baton]
    result = knowledge_agent.invoke({"messages": inputs})
    return {"messages": result["messages"][len(inputs):]}

def devops_node(state: AgentState):
    sys_msg = SystemMessage(content="""你負責執行編譯與部署工具。
    MCU 任務直接呼叫 compile_and_flash_mcu。
    MPU 任務依序呼叫 start_mpu_build -> check_mpu_build_status -> deploy_mpu_image。
    """)
    baton = HumanMessage(content="[系統] 輪到 DevOps 專家行動，請立即扣動板機執行編譯/部署工具。")
    inputs = [sys_msg] + state["messages"] + [baton]
    result = devops_agent.invoke({"messages": inputs})
    return {"messages": result["messages"][len(inputs):]}

def qa_node(state: AgentState):
    last_message = state["messages"][-1].content
    if "測試計畫" in last_message or "test plan" in last_message.lower():
        logger.info("[QA Expert] detects test plan generation requirement, initiating automated pipeline...")
        vision_context = ""
        extracted_chip = "LPI2C" 
        
        img_match = re.search(r'([a-zA-Z0-9_./\\]+\.(?:png|jpg|jpeg))', last_message, re.IGNORECASE)
        if img_match:
            img_path = img_match.group(1)
            if os.path.exists(img_path):
                logger.info(f"[QA Expert] Successfully loaded physical circuit diagram: {img_path}")
                img_base64 = get_image_base64(img_path)
                vision_prompt = [
                    SystemMessage(content="你是一位資深硬體工程師。請分析這張 i.MX93 EVK 的電源樹 (PWR TREE) 截圖，提取出畫面中的主要電源管理晶片 (PMIC) 型號。"),
                    HumanMessage(content=[
                        {"type": "text", "text": "請告訴我這張圖上的 PMIC 晶片型號是什麼？"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                    ])
                ]
                vision_result = llm.invoke(vision_prompt).content
                vision_context = f"\n[AI Circuit Diagram Visual Analysis Report]\n{vision_result}\n"
                if "PCA9451" in vision_result.upper():
                    extracted_chip = "PCA9451A PMIC I2C address and LPI2C2 memory map"
            else:
                logger.warning(f"[QA Expert] Image file not found: {img_path}")

        rag_query = f"{extracted_chip} setup in i.MX93 EVK"
        rag_context = query_nxp_knowledge_base.invoke(rag_query)

        combined_context = (
            f"實體電路圖分析狀態：\n{vision_context}\n-------------------\n"
            f"官方手冊與 Pinout MD 檔精確位址：\n{rag_context}\n-------------------\n"
            f"請撰寫對該 I2C 設備進行 Read/Write 的驗證代碼。"
        )
        
        structured_plan = generate_structured_test_plan(combined_context, last_message)
        
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "generated_tests")
        os.makedirs(output_dir, exist_ok=True)
        saved_files = []
        for case in structured_plan.test_cases:
            safe_name = case.test_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
            file_name = f"test_{safe_name}.py"
            file_path = os.path.join(output_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# Plan: {structured_plan.plan_title}\n")
                f.write(f"# Target Architecture: {structured_plan.target_architecture}\n")
                f.write(f"# Target Register/Device: {case.target_register} ({case.register_address})\n\n")
                f.write(case.test_python_script)
            saved_files.append(file_name)
        
        report_msg = f"📊 [Test plan generated successfully. {len(saved_files)} test scripts have been generated and stored in the `generated_tests` directory.\n{', '.join(saved_files)}"
        return {"messages": [AIMessage(content=report_msg)], "next_node": "FINISH"}
    else:
        sys_msg = SystemMessage(content="你負責序列埠監聽。請立即使用預設埠號呼叫 monitor_device_logs 工具。")
        inputs = [sys_msg] + state["messages"]
        result = qa_agent.invoke({"messages": inputs})
        return {"messages": result["messages"][len(inputs):]}