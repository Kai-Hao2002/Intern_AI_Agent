# AI-Driven Embedded DevOps Agent for NXP i.MX93

This project implements a fully automated, Large Language Model (LLM) based Embedded DevOps system designed specifically for the NXP i.MX93 heterogeneous multi-core architecture (Cortex-A55 + Cortex-M33). By integrating Retrieval-Augmented Generation (RAG), Multimodal Vision, and Tool Calling, the system autonomously performs compiling, flashing, run-time crash monitoring, and hardware schematic analysis, achieving a "Self-Healing" development loop.


### Project Directory Structure

```text
Intern_AI_Agent/
 │
 ├── docs/                          # Stores NXP manuals, schematics, and processed Markdown
 │   ├── processed/                 # EVK_Schematic_Pinout.md, etc.
 │   └── sensor_schematic.png       # Schematic screenshot
 │
 ├── src/                           # Core source code
 │   ├── agent/
 │   │   └── ai_agent.py            # Main AI Agent program (The Brain)
 │   │
 │   ├── tools/                     # Automation tools used by the Agent (The Limbs)
 │   │   ├── __init__.py            # Empty file, marks directory as a Python module
 │   │   ├── run_keil_tool.py       # MCU build and flash tool
 │   │   ├── run_yocto_tool.py      # MPU remote Yocto deployment tool
 │   │   └── serial_monitor_tool.py # UART crash listening tool
 │   │
 │   ├── mock/                      # Local simulation test environment (Mock Stubs)
 │   │   ├── mock_keil.py
 │   │   ├── mock_jlink.py
 │   │   └── mock_board_uart.py
 │   │
 │   └── rag/                       # Knowledge base scripts (The Memory)
 │       ├── ingest_data.py         # Reads PDF/Web to build vector database
 │       ├── query_rag.py           # Pure RAG query testing
 │       └── evaluate_rag.py        # Automated RAG accuracy evaluation
 │
 ├── chroma_db/                     # (Auto-generated) Vector database storage
 ├── flash_m33.jlink                # J-Link script
 ├── requirements.txt               # Project dependencies (LangChain, paramiko, pyserial, etc.)
 └── README.md                      # Project documentation
 
```

## 🌟 Core Features

1. **Automated Multi-Core Deployment**
   - **MCU (Cortex-M33)**: Automatically invokes the Keil MDK CLI for headless builds and integrates SEGGER J-Link for one-click flashing and verification.
   - **MPU (Cortex-A55)**: Uses SSH scripts to automatically connect to a remote server, trigger Yocto Bitbake, and flash the Image to eMMC via the NXP UUU tool.
2. **Run-time Monitoring & Self-Healing**
   - Built-in UART virtual serial port monitor that intercepts `Kernel panic` or `HardFault` in real-time during the boot process.
   - Upon catching a crash, the Agent automatically consults the knowledge base to analyze the root cause and provides specific C-code or Linux configuration fixes.
3. **RAG Hardware Knowledge Base**
   - Integrates thousands of pages of official NXP Reference Manuals, EVK User Guides, and Linux Porting Guides.
   - Accurately retrieves peripheral Base Addresses, Memory Maps, and Device Tree configurations.
4. **Multimodal Schematic Analysis**
   - Utilizing Vision models, the AI can read screenshots of physical circuit Schematics, identify Pinouts and hardware wiring, and automatically generate Test Plans complete with register initializations.

## 📁 System Architecture
- **`/src/agent`**: The core brain, utilizing LangChain to build a Tool-Calling Agent.
- **`/src/tools`**: Encapsulated DevOps automation tool modules (Keil, Yocto, PySerial).
- **`/src/mock`**: Mock scripts for local, hardware-free simulation testing, including virtual compilers and virtual boot serial ports.
- **`/src/rag`**: Scripts for Vector Database (ChromaDB) construction, querying, and automated evaluation.
  

## 🚀 快速啟動 (Quick Start)

## 🚀 Quick Start

### 1. Install Dependencies
   ```bash
   python3.10 -m venv venv
   .\venv\Scripts\activate   # Windows
   # source venv/bin/activate # macOS/Linux

   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt  
   pip freeze > requirements.txt
   docker build -t mock-yocto .
   docker run -d -p 2222:22 --name yocto-server mock-yocto
   python src/tools/run_keil_tool.py
   python src/tools/run_yocto_tool.py
   python src/mock/mock_board_uart.py
   python src/agent/ai_agent.py
   ```