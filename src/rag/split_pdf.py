import os
from pypdf import PdfReader, PdfWriter

def split_pdf_by_chapters(document_name, input_pdf, output_dir, chapter_ranges, file_prefix=""):
    """
    將大型 PDF 根據指定的頁碼範圍拆分成多個小檔案。
    Splits a large PDF into smaller files based on specified page ranges.
    """
    if not os.path.exists(input_pdf):
        print(f"❌ 找不到輸入檔案 (Input file not found): {input_pdf}")
        print(f"請確保您已將 {document_name} 放入正確的路徑。")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 建立輸出資料夾 (Created output directory): {output_dir}")

    print(f"📖 正在讀取 (Reading) {input_pdf} ... (檔案較大，請耐心等候幾秒鐘 / Large file, please wait)")
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    print(f"✅ 讀取完成 (Read complete)，總頁數 (Total pages): {total_pages}\n")

    for chapter_name, (start_page, end_page) in chapter_ranges.items():
        # 防呆機制：將使用者看到的 1-indexed 頁碼轉換為 pypdf 的 0-indexed 索引
        # Convert 1-indexed page numbers to 0-indexed for pypdf
        start_idx = max(0, start_page - 1)
        end_idx = min(total_pages, end_page)

        writer = PdfWriter()
        # 將指定範圍的頁面加入新的 PDF 寫入器 (Add pages to the writer)
        for i in range(start_idx, end_idx):
            writer.add_page(reader.pages[i])

        # 儲存拆分後的小檔案 (Save the split file)
        output_filename = os.path.join(output_dir, f"{file_prefix}{chapter_name}.pdf")
        with open(output_filename, "wb") as output_pdf:
            writer.write(output_pdf)

        print(f"✂️ 成功產出 (Successfully created): {output_filename} (Pages {start_page} to {end_page})")

if __name__ == "__main__":
    # ==========================================
    # ⚙️ 參數設定區 (Configuration)
    # ==========================================
    
    OUTPUT_FOLDER = "./docs/processed"

    # 定義要處理的文件與對應的章節 (Define documents and chapters to process)
    # 💡 請確認此處的頁碼是 PDF 閱讀器上顯示的「絕對頁碼」(包含目錄的羅馬數字頁)
    # 💡 Please ensure these are the "absolute page numbers" displayed in your PDF viewer (including TOC pages)
    
    DOCUMENTS_TO_PROCESS = {
        "NXP_iMX93_Reference": {
            "path": "./docs/i.MX_Reference_Manual.pdf",
            "prefix": "IMX93_",
            "chapters": {
                # Task 1: MCU, Debugging, and Peripheral focus
                "01_Memory_Maps": (34, 90),           # Chapter 2
                "02_System_Boot_Flow": (249, 297),    # Chapter 9
                "03_Cortex_A55": (303, 305),          # Chapter 12 (Task 2 Core)
                "04_Cortex_M33": (306, 373),          # Chapters 13, 14 (Task 1 Core)
                "05_Messaging_Unit": (585, 639),      # Chapter 20 (IPC between M33 & A55)
                "06_System_Debug_JTAG": (1272, 1290), # Chapters 24, 25 (J-Link dependency)
                "07_IOMUX_and_Pins": (1291, 1712),    # Chapters 26, 27 (Pin configuration)
                "08_GPIO": (1713, 1737),              # Chapter 28
                "09_Clock_Power_CCM_SRC": (1738, 2072),# Chapters 29, 30, 32 (Hardware bring-up)
                "10_Storage_uSDHC": (2369, 2520),     # Chapter 38 (Yocto image deployment)
                "11_USB": (2768, 2914),               # Chapter 41 (NXP UUU flashing)
                "12_LPI2C": (4753, 4822),             # Chapter 60
                "13_LPSPI": (4823, 4870),             # Chapter 61
                "14_LPUART": (4871, 4940)             # Chapter 62
            }
        },
        "Yocto_Mega_Manual": {
            "path": "./docs/Yocto_Mega_Manual.pdf", # 替換成您實際下載的 Yocto 手冊檔名
            "prefix": "Yocto_",
            "chapters": {
                # Task 2: Build System, BSP, and Testing focus
                "01_Concepts_Overview": (23, 92),     # Chapter 4
                "02_Reference_Manual": (119, 496),    # Chapter 6 (Classes, Tasks, devtool)
                "03_BSP_Guide": (497, 522),           # Chapter 7
                "04_Dev_Tasks": (523, 766),           # Chapter 8 (Bitbake, Wic, Recipes)
                "05_Kernel_Dev": (767, 832),          # Chapter 9 (Device Tree / Driver)
                "06_Test_Environment": (989, 1022)    # Chapter 14 (ptest, automated testing)
            }
        },
        "NXP_iMX93_EVK_UM": {
            "path": "./docs/EVK_Board_User_Manual.pdf", # 開發板硬體手冊路徑 / Board User Manual path
            "prefix": "IMX93_EVK_",
            "chapters": {
                # Physical board setup, test plan generation, and debugging targets
                "01_Physical_Connectors_Switches": (10, 13), # 實體接頭、跳線、按鈕與 DIP 開關 (Connectors, Jumpers, LEDs, Buttons, DIP switches)
                "02_I2C_Interface": (19, 20),                # I2C 周邊配置 (I2C interface)
                "03_Boot_Configuration": (21, 22),           # 開機模式與裝置選擇 (Boot mode and boot device configuration)
                "04_Storage_SD_eMMC_QSPI": (25, 26),         # 儲存媒介介面 (SD card, eMMC, QSPI NOR)
                "05_CAN_USB_Interfaces": (26, 27),           # CAN 與 USB 介面 (CAN and USB interfaces)
                "06_Expansion_and_Debug_JTAG": (30, 33)      # 擴充接頭、USB 除錯與 JTAG (Expansion connector, USB debug, JTAG)
            }
        },
        "NXP_iMX_Porting_Guide": {
            "path": "./docs/i.MX_Porting_Guide.pdf", 
            "prefix": "IMX_PORT_",
            "chapters": {
                # Task 2: U-Boot/Kernel 在 Yocto 中的移植與 Device Tree 基礎
                "01_Porting_Kernel_UBoot": (3, 12),     # Chapters 2 & 3: 核心與 Bootloader 移植
                "02_IOMUX_UART_SDHC_SPI": (21, 25),     # Chapters 8-11: 基礎腳位與儲存設定
                "03_I2C_Interface": (33, 35),           # Chapter 14.5: I2C 周邊掛載
                "04_Ethernet_USB": (41, 46)             # Chapters 18 & 19: 網路與 USB 介面
            }
        },
        "NXP_iMX_Linux_RM": {
            "path": "./docs/i.MX_Linux_Reference_Manual.pdf", 
            "prefix": "IMX_LNX_RM_",
            "chapters": {
                # Task 2 & Week 6: Linux 驅動架構與官方單元測試計畫 (Test Plans)
                "01_System_IOMUX_GPIO_Clock": (11, 19), # Chapter 2: 中斷、腳位、GPIO、時脈
                "02_Storage_MMC_SPI": (51, 55),         # Chapter 3: 記憶卡與 SPI 儲存
                "03_SPI_Flash": (58, 60),               # Chapter 3.5: QuadSPI/FlexSPI
                "04_ECSPI_I2C": (72, 75),               # Chapters 4.3 & 4.6: SPI 與 I2C 驅動
                "05_USB_LPUART_LPSPI": (90, 98),        # Chapters 4.9, 4.11: USB 與 UART 驅動
                "06_LPSPI": (105, 106),                 # Chapter 4.18: 低功耗 SPI
                "07_Unit_Tests_System_Storage": (270, 273), # Chapter 12: Watchdog, MMC 單元測試
                "08_Unit_Tests_Connectivity": (273, 277)    # Chapter 12: SPI, I2C, UART, USB 單元測試 (Week 6 寶藏庫)
            }
        }
    }

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

    print("\n🎉 所有指定章節拆分完成！請接著執行 build_rag.py 來建立純淨的知識庫。")
    print("🎉 All specified chapters split successfully! Proceed to run build_rag.py to build the clean knowledge base.")