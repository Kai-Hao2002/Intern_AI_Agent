# NXP i.MX 93 EVK 實體電路圖連接與配置指南 (Schematic Pinout & Configuration)

本文件定義了 i.MX 93 EVK (MCIMX93-SOM + MCIMX93-BB) 的實體硬體連接狀態、I2C 設備位址、開機指撥開關設定以及電源樹配置，作為自動化測試與驅動移植的絕對參考依據。

## 1. I2C 總線與周邊設備對應表 (I2C Device Table)

開發板上的 I2C 周邊設備與其 7-bit 設備位址 (I2C Address) 對應如下。測試與驅動程式開發必須嚴格遵守此位址設定：

### MX-I2C1 (1MHz Fm+)
* **Audio CODEC (音訊編解碼器)**: 設備型號為 WM8960，位址為 `0x1A`。
* **IMU (慣性測量單元)**: 設備型號為 LSM6DSOXTR，位址為 `0x6A`。
* **IO Expander (輸出入擴充晶片)**: 設備型號為 PCAL6524HEAZ，位址為 `0x22`。

### MX-I2C2 (1MHz Fm+)
* **PMIC (電源管理晶片)**: 設備型號為 NXP PCA9451AHN，位址為 `0x25`。此晶片負責提供 SoC 核心與周邊電源。

### FTDI-I2C (由 FTDI 晶片控制的測量總線)
* **Temperature Sensor (溫度感測器)**: 設備型號為 PCT2075，位址為 `0x48`。
* **Power Monitors (電源監控晶片 PAC1934T)**:
    * 監控點 U902: 位址 `0x11`
    * 監控點 U904: 位址 `0x12`
    * 監控點 U907: 位址 `0x13`
    * 監控點 U911: 位址 `0x14`
    * 監控點 U912: 位址 `0x15`

### USB Type-C PD PHY (掛載於多條 I2C)
* **USB-C PHY 1 (U301)**: 型號 PTN5110NHQZ，位址 `0x50`。
* **USB-C PHY 2 (U307)**: 型號 PTN5110NHQZ，位址 `0x51`。
* **USB-C PHY 3 (U401)**: 型號 PTN5110NHQZ，位址 `0x52`。

---

## 2. 開機模式與 DIP 開關設定 (Boot Mode Configuration)

i.MX 93 的開機設備由 `BOOT_MODE[3:0]` 硬體腳位決定。在進行 Yocto Image 燒錄或測試時，需確保實體 DIP 開關符合以下邏輯：

* **0000**: 從內部 Fuses 開機 (通常配合 Serial Downloader 進入 USB1/2 燒錄模式，配合 NXP UUU 工具使用)。
* **0010**: 從 **USDHC1** 開機 (實體連接至板載 **eMMC 5.1**)。
* **0011**: 從 **USDHC2** 開機 (實體連接至 **MicroSD Card** 插槽，支援 4-bit SD 3.0)。
* **0100**: 從 **FlexSPI** 開機 (實體連接至 Serial NOR Flash)。

*註：Cortex-M33 的 Low Power Boot 模式對應的開機代碼為 `1010` (eMMC) 與 `1011` (SD Card)。*

---

## 3. PMIC 電源樹配置 (PCA9451A Power Tree)

主電源管理晶片 (PCA9451A) 提供 i.MX 93 SoC 的各項關鍵電壓。在進行硬體除錯 (Hardware Bring-up) 時，應測量以下電壓是否正常輸出：

* **BUCK1/3 (0.85V)**: 供應 `VDD_SOC` (SoC 核心電壓，最大 4000mA)。
* **BUCK4 (3.3V)**: 供應 `NVCC_GPIO` 與 `VDD_USB_3P3` (通用 IO 與 USB 3.3V，最大 3000mA)，並透過 Load Switch 供應 SD Card 電源。
* **BUCK5 (1.8V)**: 供應 `VDD_ANA_1P8` 等類比電源 (最大 2000mA)。
* **BUCK6 (1.1V)**: 供應 `VDD2_DDR` (LPDDR4/X 記憶體電壓)。
* **BUCK2 (0.6V)**: 供應 `VDDQ_DDR` (LPDDR4x 專用 VDDQ 電壓)。
* **LDO1 (1.8V)**: 供應 `NVCC_BBSM_1V8` (系統備用電源區域)。