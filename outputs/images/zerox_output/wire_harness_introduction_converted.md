# Wire harness
# Introduction

1

# 目錄

• 認識 NB 內部用線

• EDP cable 介紹與 cable 的組成

• Cable 成本分析

• 視圖要素

2

# 認識 NB

通常會由頂至底依序以 A 、 B 、 C 、 D 件來稱呼筆電機殼

> A 件就是筆電上蓋外側部分
> B 件則是上蓋內側、螢幕邊框部分
> C 件為底座內側，也就是鍵盤以及觸控板的組件
> D 件則是底座外側

3

# 拆卸 D 件後：

[Image shows the internal components of a disassembled laptop with labeled parts in Chinese and English:]

- **hinge** (鉸鏈)
- **antenna** (天線)
- **EDP cable** (EDP 線纜)
- **FFC** (排線)
- **NB 內部用線 實例照** (筆記本內部用線實例照片)

The image displays the motherboard, cooling fan, heat sink, memory modules, and various cables and connectors inside the laptop chassis. At the bottom right, there's a battery with warning labels and regulatory information.

**4**

# NB 內部用線種類

NB 內部用線依用途與尺寸空間的不同，通常可見有以下三類：

| | 單價 | 優點 | 缺點 |
|---|---|---|---|
| Wire Harness | 適中 | 完全客製化外觀與功能定義 | cable 厚度最厚，價格依設計波動大 |
| FPC | 高貴 | 最薄，可輕微彎折 | cable 厚度最薄，單價高 |
| FFC | 便宜 | 可彎折，價格便宜 | 功能可變性最低 |

➤ Cable 是不同部件功能連接的橋樑，若說主板上的 CUP 是 NB 的心臟，
將螢幕與主板連接的 cable 就稱為 EDP cable or LCD cable，亦是 NB 中
不可或缺的重要材料。

➤ 而 EDP cable 根據 panel 與外觀限制的不同，大致分為以下兩種設計：
1. 純 wire harness
2. 複合設計：wire harness+FFC 或 wire harness+FPC

5

# NB 內部用線—依功能性區分

A. Display function 的 EDP cable：
俗稱大線，連接螢幕顯示的用途，缺一不可的重要元件，有以下三種設計：
1. 純 wire harness
2. 複合設計：wire harness+FFC
3. 複合設計：wire harness+FPC

B. Others function cable：
俗稱小線，如 USB, Touch, battery, audio, microphone, Bluetooth, IO interface....etc 用來連接內部各種不同功能版，依 NB 規格有時為選配，設計上常見有：
1. wire harness
2. FPC
3. FFC

[Image shows various cable types including FPC and FFC examples]

6

# Cable 的組成

Cable 的組成材料大致可分為三類：

1. Connector 連接器
2. Wire 線材
3. Assistant material 輔料

複合設計的 Cable 組成材料還可以看到：

1. FPC
2. FFC
3. 開關 or 其他可以結合線材設計的元件，如 LED, 風扇… etc

[7]

# Component Diagram

![Circuit diagram showing various components with labels and arrows pointing to different parts]

**FPC** - pointing to a flexible printed circuit component

**Assistant material** - pointing to supporting material components

**connector** - pointing to connection points (appears twice in the diagram)

**inside: wire  
outside: assistant material** - describing the internal structure with wire inside and assistant material outside

The diagram shows the assembly and connection of electronic components including FPC (Flexible Printed Circuit), connectors, and assistant materials with internal wiring structure.

**8**

# Connector 連接器

Cable 上會用到的連接器，依加工方式分為：

➤焊接式 (solder style)  
➤刺破式 (puncture style)  
➤穿端子 (IDC housing)  
➤Board to Board

[THIS IS FIGURE: Image showing various types of connectors including a white connector with multiple colored wires, coiled cables with connectors, and board-to-board connectors]

9

# Solder Bar

## solder
![Image showing electronic components including a white PCB with multiple connector slots and black connectors with gold pins]

![Image showing a connector with multiple wires (black, red, and other colors) soldered to pins]

![Diagram showing a cross-section view of a solder bar connection]

## puncture
![Image showing several black plastic connectors with multiple pin slots of varying sizes]

## crimping
![Image showing white plastic connectors and a strip of metal pins/contacts]

**10**

# Wire 線材

依 UL 防火規格的不同（一般均符合 VW-1）有相應的線徑與材質，NB 內部線使用的為 19C 的極細線：

➤ 極細電子線 UL10064
➤ 極細同軸線 UL10005

## 電子線

[Diagram showing cross-section of electronic wire with labels:]
- 外被
- 芯線

常用 #34 、#36

## 同軸線

[Diagram showing cross-section of coaxial cable with labels:]
- 外被
- 銅箔
- 編織
- 內被
- 芯線

常用 #40 、#36

11

# Assistant material 輔料

常用輔料如下列：

**A. 絕緣 & 保護材料：**
➤ 醋酸布 Acetate type
➤ KA00

**B. EMI 材料**
➤ 導電布 Conductive type
➤ 導電背膠 Conductive adhesive
➤ 導電泡棉 Gasket

**C. Others：Mylar, 背膠 Adhesive, 標籤 Label, 磁環 Core....etc**

12

# Cable 的成本分析

當收到 RFQ 詢價需求時，不論是否有提供圖面 or 示意圖，或只有文字敘述：

首要確認以下項目：

A. 連接器料號：有無供應商與料號

B. 線材種類：電子線 or 同軸線 or 混線設計

C. 線長 & 用線數 (pin define)

D. 外觀說明

13

# Cable 的成本分析

次要確認以下項目：

a) 連接器 & 線材要求是否可以搭配加工

b) 是否可以使用替代料件

c) 用線數，長度，及當多頭設計時，各分段的長度

d) 外觀材料：導電布，醋酸布（含各分段長度）

e) 外觀要求：束圓？打扁？複雜設計？

f) 有無拉帶：種類與數量（醋酸拉帶／導電布拉帶）

g) 有無特殊材料：如穿 core, hinge, FPC, FFC, 開關，吸波材…etc

h) 其他測試要求：如高頻測試，高低溫測試

14

# Cable 的成本分析

## Cable 報價的組成：
➤ 材料成本：連接器、線材、輔料  
➤ 工時成本：廠內生產、外發加工  
➤ 管銷與利潤：品管，檢驗，損耗，包裝，良率，利潤

## 影響價格高低因素：
➤ 多頭設計：俗稱一個連接器為一個頭，越多頭價格越高  
➤ 外觀設計：打扁比束圓貴，外觀越複雜越貴，外觀變換分越多段亦越貴，  
（如：束圓 ----> 打扁 ----> 轉彎 ----> 束圓 ----> 焊接 FFC----> 打扁）  
➤ 連接器：使用替代料較便宜，專用料較貴且議價空間小  
➤ 焊接式加工比壓接式工時高，0.4pitch 比 0.5 pitch 工時高  
➤ 線位是否順線：相對順線的設計工時較低且良率高

15

# Cable 設計實例：

## 便宜的設計：

[Image shows a simple cable design with basic connectors]

## 高貴的設計：

[Image shows more sophisticated cable designs with multiple connectors and components, including what appears to be ribbon cables and specialized connectors]

16

# 視圖要素

✓ CONN 方向，拉帶 & 膠面方向  
✓ PIN 1 的位置 & PIN DEFINE  
✓ 材料廠商 & 材料料號  
✓ 料號，品名 （客戶料號 & 我司料號）  
✓ 尺寸  
✓ 公差  
✓ 版本  
✓ 屬性（環保屬性，有鹵無鹵…）  
✓ 特殊要求（TDR，加工要求…）

17

THE END

18