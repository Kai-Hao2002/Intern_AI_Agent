# src/agent/state.py
import operator
from typing import Annotated, Literal, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    """
    定義整個 Multi-Agent 系統共享的全局狀態
    Define the global state shared by the entire Multi-Agent system.
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_node: str
    mode: str          # 核心：控制實驗組 "B1", "B2", "B3", "PROPOSED_MAS"
    retry_count: int   # 記錄除錯迴圈次數
    iteration_count: int      # 記錄「修改->編譯」的迴圈次數 (對應 k)
    build_success: bool       # 記錄當前編譯狀態
    hil_test_passed: bool     # 記錄硬體迴圈 (UART) 測試是否通過
    total_tokens: int         # 記錄 Token 消耗 (用於計算 E_token)

class RouteDecision(BaseModel):
    """
    主管節點路由決策的強制結構化輸出
    Forced structured output of routing decisions by the supervisor node
    """
    next_node: Literal["Knowledge_Expert", "DevOps_Expert", "QA_Expert", "ZeroShot_Expert", "FINISH"] = Field(
        description="Determine the next execution node. If the task is complete, send a FINISH response."
    )