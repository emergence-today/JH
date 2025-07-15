# 常规外部线设计参考

# 重点制程 EMI 管控:

| No | 管控项目 | 管控标准 | 图示 |
|----|---------|----------|------|
| 1 | 马口铁结构 | 1.两件式锐压+点焊<br>2.材质:镀锡铁(验证镀锡材质配比必须项) | [图示：三个不同的金属结构示例，最右侧有蓝色圆圈标记] |
| 2 | 网尾神合高度&外观 | 高度Spec:<br>以厂商实际结构尺寸定义(需满足锐压外观要求)<br>外观要求:<br>1.不允许马口铁领域木可变形<br>2.神件无异样对木可有间隙 | [图示：两个对比图像，一个标记"神合OK"，另一个标记"神合NG"] |
| 3 | 网尾紧密度检验 | 上下左右90°摇摆检验<br>线材与铁壳无间隙 | [图示：展示检验过程的多个步骤图] |
| 4 | 上下铁壳贴合 | 神合后间隙 ≤ 0.1mm<br>(确保上下铁壳完全贴附) | [图示：显示铁壳贴合检查的多个角度] |
| 5 | 铜箔外漏尺寸 | 网尾铜箔露外漏0.5-2mm | [图示：测量铜箔外漏的具体示例] |
| 6 | 低电阻测试 | 低电阻 ≤ 100mΩ<br>(低电阻值越小讯号损失越小) | [图示：电阻测试设备和测试过程] |
| 7 | 线材铝箔覆盖率 | 铝箔覆盖率MIN 40%<br>(铝箔好坏直接影响屏蔽性) | [图示：线材横截面图和覆盖率示意图] |
| 8 | 线材编织网密度 | 编织覆盖 ≥ 85%<br>(编织网密度关键越大,讯号损失越小) | [图示：编织网密度的检测和标准示例] |

# 测试管控：

## 1号道里兰秒对比
| 接口 | 海信 | 今信 | 索尼 | 铁欧 | 台信 | 正大 | 对比差异 | WZ参数 |
|------|------|------|------|------|------|------|----------|--------|
| DP | 2Ω | 2Ω | 2Ω | 2Ω | 2Ω | 3Ω (MAX) | | |
| HDMI | 2Ω | 2Ω | 2Ω | 2Ω | 2Ω | 3Ω (MAX) | 各彩电差异普昔 | 参数调一般考虑：20 |
| Type-C | 2Ω | 2Ω | 2Ω | 2Ω | 2Ω | 3Ω (MAX) | | |
| USB3.0 | 2Ω | 2Ω | 2Ω | 2Ω | 2Ω | 3Ω (MAX) | | |

## 2输出让许秒对比
| 接口 | 海信 | 今信 | 索尼 | 铁欧 | 台信 | 正大 | 对比差异 | WZ参数 |
|------|------|------|------|------|------|------|----------|--------|
| DP | 10MΩ | 10MΩ | 10MΩ | 5MΩ | 20MΩ | 20MΩ | | |
| HDMI | 10MΩ | 10MΩ | 10MΩ | 5MΩ | 20MΩ | 20MΩ | 各彩单峙公这里普昔 | 参数调一般考虑：10MΩ |
| Type-C | 10MΩ | 10MΩ | 10MΩ | 5MΩ | 10MΩ | 20MΩ | | |
| USB3.0 | 10MΩ | 10MΩ | 10MΩ | 5MΩ | 20MΩ | 20MΩ | | |

## 3继电更起分分对比
| 接口 | 海信 | 今信 | 索尼 | 铁欧 | 台信 | 正大 | 对比差异 | WZ参数 |
|------|------|------|------|------|------|------|----------|--------|
| DP | NA | 5s | NA | 2s | NA | 0.1s | | |
| HDMI | NA | 5s | NA | 2s | NA | 0.1s | 各彩单峙公这里普昔 | 除正大都嫌一般考虑：2s |
| Type-C | NA | NA | NA | 2s | NA | 0.1s | | |
| USB3.0 | NA | 5s | NA | 2s | NA | 0.1s | | |

## 4半年门-门热时度秒高对比
| 接口 | 海信 | 今信 | 索尼 | 铁欧 | 台信 | 正大 | 对比差异 | WZ参数 |
|------|------|------|------|------|------|------|----------|--------|
| DP | T2最低接管15° | T2十子接管60° 8~10cm处 | T1=NA T2-T3=90° | T2十子接管10° 金管8~10cm处 | 不需考虑管 | 接管60° | | |
| HDMI | T2最低接管15° | T2十子接管60° 8~10cm处 | T1=NA T2-T3=90° | T2十子接管10° 金管8~10cm处 | 不需考虑管 | 接管60° | 各彩厂商T1-T3条件好 性况不 | 1.T1太低接规候诚 2.T2十子接管15°，8~10cm处 3.T3十子接管60°，8~10cm处 |
| Type-C | T2最低接管15° | T2十子接管60° 8~10cm处 | T1=NA T2-T3=90° | T2十子接管10° 金管8~10cm处 | 不需考虑管 | 接管60° | | |
| USB3.0 | T2最低接管15° | T2十子接管60° 8~10cm处 | T1=NA T2-T3=90° | T2十子接管10° 金管8~10cm处 | 不需考虑管 | 接管60° | | |

## 5差自相应考对比
| 接口 | 海信 | 今信 | 索尼 | 铁欧 | 台信 | 正大 | 对比差异 | WZ参数 |
|------|------|------|------|------|------|------|----------|--------|
| DP | | | | | | | | |
| HDMI | 距离外端8~10cm | 距离外端15~20cm | 距离外端10cm | 距离外端10~15cm | 距离外端8cm | 距离外端10cm | 各彩范有差异的重点里 考虑然 | 仅避量一方距离外端距离8~10cm |
| Type-C | | | | | | | | |
| USB3.0 | | | | | | | | |

## 6成只有温度条高对比
| 接口 | 海信 | 今信 | 索尼 | 铁欧 | 台信 | 正大 | 对比差异 | WZ参数 |
|------|------|------|------|------|------|------|----------|--------|
| DP | 60° | 90° | 90° | 60° | 60° | 60° | | |
| HDMI | 90° | 90° | 90° | 60° | 60° | 60° | 各彩化温条管更公当考 虑 | 接规海支最优行 |
| Type-C | 90° | 90° | 60° | 60° | 60° | 60° | | |
| USB3.0 | 60° | 90° | 90° | 60° | 60° | 60° | | |

## 7成只有单度条高对比
| 接口 | 海信 | 今信 | 索尼 | 铁欧 | 台信 | 正大 | 对比差异 | WZ参数 |
|------|------|------|------|------|------|------|----------|--------|
| DP | NA | NA | 90° | NA | NA | NA | | |
| HDMI | NA | NA | 90° | NA | NA | NA | 1.各彩范还不时给定 2.接规角度一致 | 1.意思如许增加档度 2.接规角度十字90° |
| Type-C | 60° | NA | 60° | NA | NA | NA | | |
| USB3.0 | NA | NA | NA | NA | NA | NA | | |

## 8单子精对比
| 接口 | 海信 | 今信 | 索尼 | 铁欧 | 台信 | 正大 | 对比差异 | WZ参数 |
|------|------|------|------|------|------|------|----------|--------|
| DP | ASUS | DELL | 三星 | HP | DELL | HP/LG | | |
| HDMI | Dell | DELL | 三星 | HP | DELL | HP/DELL | 各彩三只产分理考虑一统一 | 经规彩对年：当线海学厂商务，任何国外著名优秀彩线海学厂商， |
| Type-C | HP/Dell | DELL | BENQ | HP | DELL | HP/DELL | | 意识彩公省至公DELL作公司他 |
| USB3.0 | NA | NA | NA | NA | NA | NA | | |

# 各类别外部线介绍；

## 1.RGB 线材介绍

## 2.DVI 线材介绍

## 3.HDMI 线材介绍

## 4.DP 线材介绍

## 5.TPYE-C 线材介绍

## 6.USB2.0 线材介绍

## 7.USB3.0 线材介绍

## 8.AUDIO 线材介绍

# RGB 线材简介

显卡所处理的信息最终都要输出到显示器上，显卡的输出接口就是电脑与显示器之间的桥梁，它负责向显示器输出相应的图像信号。CRT 显示器因为设计制造上的原因，只能接受模拟信号输入，这就需要显卡能输出模拟信号。VGA 接口就是显卡上输出模拟信号的接口，VGA（Video Graphics Array）接口，也叫 D-Sub 接口。虽然液晶显示器可以直接接收数字信号，但很多低端产品为了与 RGB 接口显卡相匹配，因而采用 RGB 接口。RGB 接口是一种 D 型接口，上面共有 15 针空，分成三排，每排五个。

![Image shows a VGA cable with blue connectors on both ends - these are typical D-Sub/VGA connectors with the characteristic trapezoidal shape and multiple pins visible]

# RGB 用途

![RGB cable connection diagram showing various devices connected in a circle around a central blue VGA cable, including desktop computer (電腦), laptop (電記本), Xbox 360, PS3 (電玩PS3), monitor (螢幕器), projector (投影儀), LCD display (顯示器), and TV (電視)]

主要應用在數字電視、計算機、投影儀、高清播放器、攝像機
DVD 播放器、監視器、遊戲機等等。

# RGB 线材结构

## 1.线材蓝图

[THIS IS DIAGRAM: Technical drawing showing RGB cable structure with following labeled components:]

- **模具编号编**
- **线位表** (Wire position table showing color codes and positions 1-16)
- **材料表** (Materials table)
- **会签栏** (Approval section)
- **标题栏** (Title block)

### 线位表内容:
- CIRCUIT DIAGRAM
- P1 (wire colors including RED/COAX CORE, OPEN/COAX CORE, BLUE/COAX CORE)
- GAP positions 4-6
- Various color codes (BLACK, RED/COAX SHIELD, OPEN/COAX SHLD, BLUE/COAX SHLD, WHITE, BROWN, GREEN, ORANGE, YELLOW, BLUE, VIOLET)

### 材料表内容:
| NO. | ITEM | DESCRIPTION | Q'TY | UNIT |
|-----|------|-------------|------|------|
| 5 | COVER | ATTACH JUST COVER | 2 | PCS |
| 6 | CORE | CORE #5∅0.315mm*48*35 | 2 | PCS |
| 3 | SCREW | THUMB SCREW 4-40NC COLOR PANTONE 661C | 2 | PCS |
| 5 | MOLDING | OUTER MOLDING COLOR PANTONE 661C | 2 | PCS |
| 4 | MOLDING | OUTER MOLDING COLOR BLACK | N/A | G |
| 1 | CASE | INNER CASE | 2 | PCS |
| 2 | CONN | D-SUB CONNECTOR 3R-15P (WSOLDER端子付) (雌性) | 2 | PCS |
| 7 | CABLE | CABLE UL20276 (1C)(AAW*26AWG+AF+24*60)*50AWG+AR(AL) COLOR BLACK OD:5.2 | N/A | MM |

### 注意事项:
1. P1&P2端的电平控制条件是正确
2. P1&P2端的电缆接続部份, 端口线纳部锁定数量三年以上
3. P1&P2端的电缆接续导体的另一端的连接线宽度不介全条
4. 测试电源:DC 300V, 绝缘阻抗:10MΩ,导通阻抗:2Ω以下
5. 径性阻抗: 75±5Ω
6. 重量: P1=P2=21G

# 2. 半成品線圖示

![線材實物圖](左側顯示黑色電纜的橫截面實物照片)

![RGB 線材結構圖](右側顯示電纜橫截面結構示意圖，標注了各個組件：)
- 被覆
- 編織
- 鋁箔  
- 地線
- 4 (Component B)
- 鋁箔
- 1 (Component C)
- 7
- 8
- 9 (Component A)

**RGB 信号传输线材结构：**

红、绿、蓝三色同轴线，同轴线的结构比较统一，为增强屏蔽效果会增加一层编织和护套以或增加地线。同轴线的绝缘一般使

（1）用发泡 PE （FM-PE）；

（2）护套使用 PVC ；

（3）导体使用裸铜或镀锡铜。

![Cable cross-section diagram showing components labeled in Chinese]

**外被**: 主要的材料為 PVC 、PE 、PP 還有試樣無齒等。

**編織**: 在線材外面編上一層鋁鎂鋁絲，以起到屏蔽的作用。編織的錠數分為 16 錠和 24 錠。

**鋁箔**: 由 AL 和聚酯薄膜粘合而成。

**芯線**: 發泡線、鍍錫銅絞線、FPE 料、HDPE 以及無齒色母。
**電子線**: 鍍錫銅絞線、FPE 料、HDPE 以及無齒色母。
**地線**: 多股鍍錫銅編絞合而成

# 3. 連接頭圖示

![Connector diagram showing cable with blue connectors and detailed breakdowns of components]

**外模: PVC**

**鐵殼: SPCC 馬口鐵**

**端子: 銅 鍍金**

**膠芯: PBT**

**端子: 銅 鍍錫**

# 4. PIN 角定義

![VGA connector pin diagram showing a 15-pin D-sub connector with labeled pins]

**VGA**

Pin assignments (clockwise from top):
- Pin 1: 紅基色
- Pin 5: 地出號
- Pin 6: 紅地
- Pin 10: 白測試
- Pin 11: 地出號
- Pin 15: 地出號

Additional pins labeled:
- 藍基色
- 綠基色
- 紅基色
- 垂直
- 綠地
- 紅地
- 數字地
- 垂直步
- 行同步
- 地出號
- 地出號

# DVI 线简介

DVI 是基于 TMDS(Transition Minimized Differential Signaling)，转换最小差分信号技术来传输数字信号，TMDS 运用先进的编码算法把 8bit 数据（R、G、B 中的每路基色信号）通过最小转换编码为 10bit 数据（包含行场同步信息、时钟信息、数据DE、纠错等），经过 DC 平衡后，采用差分信号传输数据，它和 LVDS、TTL 相比有较好的电磁兼容性能，可以用低成本的专用电缆实现长距离、高质量的数字信号传输。TMDS 技术的连接传输结构如图 1 所示。数字视频接口（DVI）是一种国际开放的接口标准，在 PC、DVD、高清晰电视（HDTV）、高清晰投影仪等设备上有广泛的应用。

![DVI connector image showing two DVI cable connectors against a blue background]

# DVI 線應用

![DVI cable application diagram showing a DVI cable in the center connected to 5 different devices in circular arrangement: ①台式電腦 (desktop computer), ②筆記本 (laptop), ③DVD player, ④投影儀 (projector), and ⑤高清電視 (HDTV)]

DVI 適合在液晶顯示器、筆記本電腦、LCD、PC 使用的監視器、投影儀以及數位家電電器等數位產品中。

# DVI 线材结构

## 1. 线材蓝图

| REV. | ECN NO. | DATE | CHECKED BY | DESCRIPTION |
|------|---------|------|------------|-------------|
| A | | 2018/7/18 | Jerry | NEW DESIGN |

**P1:DVI_DM(18+1)** ←→ **5000±100** ←→ **P2:DVI_DM(18+1)**

### 连接器规格图
- 外壳尺寸：48±0.5 × 35±0.5
- 线缆标识：⌀6±0.3
- 引脚编号：1-24
- 屏蔽层标识：⑤⑥、②④⑤、⑤④③

### 线位表
| P1:DVI_DM(18+1) | P2:DVI_DM(18+1) | 线色 |
|-----------------|-----------------|------|
| 2 | 2 | 红 |
| 3 | 3 | 蓝 |
| 1 | 1 | 白 |
| 10 | 10 | 绿 |
| 11 | 11 | 紫 |
| 9 | 9 | 红 |
| 18 | 18 | 黄 |
| 19 | 19 | 灰 |
| 17 | 17 | 白 |
| 25 | 25 | 蓝 |
| 22 | 22 | 紫 |
| 24 | 24 | 绿 |
| 6 | 6 | 红 |
| 7 | 7 | 白 |
| 15 | 15 | 蓝 |
| 14 | 14 | 黄 |
| 16 | 16 | 绿 |
| SHELL | SHELL | 屏蔽 |

### 成品意图
[橙色标识框显示"成品意图"]

### RoHS 2.0 Compliant
[标识：无红磷]

### 材料表
| ① | HOUSING | 2×3.Positions housing | NYLON | 1 | PCS |
| ② | OUTER-MOLD | PVC 4# BLACK | 2# | 1 | KG |
| ③ | INNER-MOLD | PE CLEAR | 1 | 1 | KG |
| ④ | DVI-CONN | DVI DM(18+1)标准端子材质铜镀金40μ"电子线路连接用,抗磨耐用 | 2 | SET |
| ⑤ | DVI-CONN | DVI DM(18+1)标准端子材质铜镀金40μ"电子线路连接用,抗磨耐用 | | |
| ⑥ | CABLE | UL2919-28AWG*2+D+2C+18cUL2725*6AWG*3+D*AD | | PCS |
| | | (X*7.3mm)24cL Jacket材质:铜线镀银+PE绝缘+编织屏蔽 | | |

| ITEM | PART | DESCRIPTION | Q'TY | UNIT |
|------|------|-------------|------|------|
| CUSTOMER P/N: | | JH-HAW INDUSTRIAL CO., LTD |
| | | JH-HAW INDUSTRIAL CO., LTD |
| | | JH-HAW OPTO-ELECTRICAL |

### 注意事项
**Note:**
1. 支持1920*1080P以上分辨率高清画质
2. 内置螺蚊螺丝，牢固有效屏蔽电磁
3. 芯片型号：S1215
4. 本产品执行标准为公司Q/CK75J

| TOLERANCE | JH P/N: P113A180001 |
|-----------|---------------------|
| ±1-±0.1 | CUSTOMER: CH222 |
| ±1-±0.5 | |
| ±1-±2.3 | MODEL: |
| ±81-±3.0 | SCALE: | UNIT: mm |
| ANGLE:±2° | 中 -□- | DRAW: |

| APPROVED | Svensson |
|----------|----------|
| CHECKED | Phyllis |
| DRAW | Jerry |

| 标题栏 |
|--------|
| SHEET: 1/2 |
| DRAWING NO: |
| DB7370 |

# 2. 半成品线圈展示

## 线材实物图

[Left side shows a photograph of a cable cross-section with multiple colored wires bundled together in a black outer sheath]

## DVI 线材结构图

[Right side shows a technical diagram of the cable structure with labeled components]

- 被覆
- 编织铝箔
- 4P
- 1
- 5
- 1P(component A)
- 2 (component B)
- 3
- 4
- 2P
- 地线

**DVI 数字信号传输线材 结构：**
**4 Twinax signal wires+5C single wires.**

![Cable cross-section diagram showing components labeled in Chinese]

**外被**: 主要的材料為 PVC、PE、PP 還有試樣無鹵等。

**編織**: 在線材外面編上一層鋁鎂絲，以起到屏蔽的作用。編織的錠數分為 16 錠和 24 錠。

**鋁箔**: 由 AL 和聚酯薄膜粘合而成。

**芯線**: 發泡線、鍍錫銅絞線、FPE 料、HDPE 以及無鹵色母。
**電子線**: 鍍錫銅絞線、FPE 料、HDPE 以及無鹵色母。
**地線**: 多股鍍錫銅編絞合而成

# 3. 连接头图示

![Connector diagram showing various components of a cable connector system]

**外模：PVC**

**铁壳：SPCC 马口铁**

**连接头**

**端子：铜 镀金**

**胶芯：PBT**

**端子：铜 镀锡**

# 4. PIN 角定義

## DVI-I 连接器

| 针脚 | 功能 | 针脚 | 功能 |
|------|------|------|------|
| 1 | TMDS 数据 2- | 13 | TMDS 数据 3+ |
| 2 | TMDS 数据 2+ | 14 | +5V 直流电源 |
| 3 | TMDS 数据 2/4 屏蔽 | 15 | 接地 (+5 回路) |
| 4 | TMDS 数据 | 16 | 热插拔检测 |
| 5 | TMDS 数据 | 17 | TMDS 数据 0- |
| 6 | DDC 时钟 | 18 | TMDS 数据 0+ |
| 7 | DDC 数据 | 19 | TMDS 数据 0/5 屏蔽 |
| 8 | 模拟垂直同步 | 20 | TMDS 数据 5- |
| 9 | TMDS 数据 1- | 21 | TMDS 数据 5+ |
| 10 | TMDS 数据 1+ | 22 | TMDS 时钟屏蔽 |
| 11 | TMDS 数据 1/3 屏蔽 | 23 | TMDS 时钟+ |
| 12 | TMDS 数据 3- | 24 | TMDS 时钟- |
| C1 | 模拟垂直同步 | C4 | 模拟水平同步 |
| C2 | 模拟绿色 | C5 | 模拟接地 (RGB 回路) |
| C3 | 模拟蓝色 | | |

# 5.RGB 与 DVI 区别

DVI 接口的传输信号采用全数字格式，与之对应的是采用模拟信号的 VGA 接口。VGA 和 DVI 的区别，首先 VGA 模拟信号的传输比较麻烦，首先是将电脑内的数字信号转换为模拟信号，将信号发送到 LCD 显示器，而显示器再将该模拟信号转换为数字信号，形成画面展示在大家面前。正因为如此，中间的信号丢失严重，虽然可以通过软件的方法修复部分画面，但是随着显示器的分辨率越高画面就会越模糊。一般模拟信号在超过 1280×1024 分辨率以上的情况下就会出现明显的误差，分辨率越高越严重

DVI 数字接口可以直接将电脑信号传输给显示器，中间几乎没有信号损失，不过在 800×600 这种分辨率下，和模拟信号的效果几乎没有差别，这也就是很多人觉得 DVI 接口没有用处的原因。但是在 1280×1024 以上分辨率的情况下，DVI 数字接口的优势就表现出来了，画面依旧清晰可见，而 VGA 接口则出现字迹模糊的现象。DVI 接口最高可以提供 8GPS 的传输率，实现 1920×1080/60Hz 的显示要求，高分辨率不仅能在 3D 电影特效泛滥的今天提供最佳电影画质，更是 3D 图形制作者的基本要求，因此 DVI 接口的普及将会是数字时代发展的必然趋势

![Image showing DVI and VGA cable connectors - DVI connector on the left (larger, rectangular with many pins) and VGA connector on the right (smaller, blue, trapezoid-shaped with pins)]

# HDMI 线材简介

HDMI 线是高清晰多媒体接口线的缩写，
能高品质地传输未经压缩的高清视频和多声
道音频数据，最高数据传输速度为 5Gbps。
HDMI 线支持 5Gbps 的数据传输率，最远可
传输 30 米，足以应付一个 1080p 的视频和
一个 8 声道的音频信号。而因为一个 1080p
的视频和一个 8 声道的音频信号需求少于
4GB/s，因此 HDMI 线还有很大余量。这允
许它可以用一个电缆分别连接 DVD 播放器，
接收器和 PRR。此外 HDMI 支持
EDID，DDC2B，因此具有 HDMI 的设备具有
"即插即用"的特点，信号源和显示设备之
间会自动进行"协商"，自动选择最合适的
视频／音频格式。

[THIS IS FIGURE: Image of a black HDMI cable with connectors on both ends]

# HDMI 线用途

![HDMI cable usage diagram showing various devices connected to a central HDMI connector, including gaming consoles, digital cameras, projectors, VR headsets, laptops, tablets, smartphones, and other multimedia devices]

主要应用于等离子电视、高清播放机、液晶电视、背投电视、投影机、DVD 录/放影机、D-VHS 录/放影机及数位影音显示装置的视频及音频信号传输。

# HDMI 线材结构

## 1. 线材蓝图

[THIS IS FIGURE: Technical diagram showing HDMI cable structure with various components including:]

- P1 and P2 connectors on both ends
- Cable specifications showing "Cable print: FH-B877-WM STYLE 20276 80°C 30V VW-1 JI-HAW"
- Component details and pin configurations
- Cross-sectional views of connectors
- Technical specifications table

### 成品示意图
[Orange box highlighting product overview section]

### 注意事项
[Orange box with warning/note section containing technical specifications in Chinese]

### 线位表
[Orange box containing pin assignment table with signal mappings]

### 材料表
[Orange box showing material specifications table]

### 标题栏
[Orange box in bottom right showing title block with part numbers and specifications]

### 无卤素 RoHS 2.0 Compliant
[Certification marks shown on right side]

观察线材成品蓝图，线材是由半成品的线缆和连接器组装而成。

# 半成品線圖示

## 線材實物圖 → 線材結構圖

[THIS IS FIGURE: Image showing a cross-section of a cable on the left with an arrow pointing to a technical diagram on the right showing the internal wire structure with various labeled components including outer jacket, shielding, and internal wire pairs]

## HDMI 線材常規結構：

**5 Twinax signal wires+4C single insulated wires 。**

**該結構與 DP High-bit-rate 線材結構完全相似，只是特性測試不同。**

# Cable Components

![Cable cross-section diagram showing various components labeled in Chinese]

**外被**: 主要的材料為 PVC、PE、PP、TPE 還有試樣無鹵等。

**編織**: 在線材外面編上一層鋁鎂絲，以起到屏蔽的作用。編織的錠數分為 16 錠和 24 錠。

**鋁箔**: 由 AL 和聚酯薄膜貼合而成。

**芯線**: 發泡線、鍍錫銅絞線、FPE 料、HDPE 以及無鹵色母。
**電子線**: 鍍錫銅絞線、FPE 料、HDPE 以及無鹵色母。
**地線**: 多股鍍錫銅裸絞合而成

---

Components labeled in the diagram:
- 電子線 (Electronic wire)
- 鋁箔 (Aluminum foil)
- 外被 (Outer jacket)
- 編織 (Braiding)
- 芯線 (Core wire)
- 地線 (Ground wire)

# 3. 連接頭圖示

![Cable connector diagram showing HDMI cables and detailed views of connector components]

外殼：PVC/
TPE

鐵殼：馬口鐵

連接頭：由膠芯、殼体、
端子組成

![USB connector components diagram with Chinese labels]

鐵殼：鋅合金，表面處理

膠芯：LCP（黑色）

錫：使用直徑 0.60mm 無鉛環保錫絲

主體：LCP（黑色）+C5191(HV180-210),T=0.20 ± 0.02。

端子：磷氯銅

# 4.PIN 角定義

## HDMI 端子

```
热插拔识别      19 ————————————— 18  +5V电源
DDC/CEC接地    17 ————————————— 16  SDA
SCL           15 ————————————— 14  保留
CEC           13 ————————————— 12  TMDS时钟-
TMDS时钟屏蔽   11 ————————————— 10  TMDS时钟+
TMDS数据0-     9 ————————————— 8   TMDS数据0屏蔽
TMDS数据0+     7 ————————————— 6   TMDS数据1-
TMDS数据1屏蔽   5 ————————————— 4   TMDS数据1+
TMDS数据2-     3 ————————————— 2   TMDS数据2屏蔽
TMDS数据2+     1 ————————————— 
```

(电缆内，但是NC来留在装置上)

# DP 線材簡介

DP （DisplayPort）是一种高清数字显示接口标准，可以连接电脑和显示器，也可以连接电脑和家庭影院。2006年5月，视频电子标准协会(VESA)确定了1.0版标准，并在2008年升级到1.1版，提供了对HDCP的支持，2.0版也计划在今年推出。作为HDMI和UDI的竞争对手和DVI的潜在继任者，DisplayPort赢得了AMD、Intel、NVIDIA、戴尔、惠普、联想、飞利浦、三星、aoc等业界巨头的支持，而且它是免费使用的。

[Image shows a black DisplayPort cable with connectors on both ends]

# DP 線用途

![DP Cable Usage Diagram showing various devices with DP ports connected via DP cable to displays with DP ports]

- 帶DP接口的主机 (Desktop computer with DP port)
- 帶DP接口的筆記本 (Laptop with DP port)  
- 帶DP接口的顯卡設備 (Graphics card with DP port)
- 帶DP接口的輸入設備 (Input device with DP port)
- 帶DP接口的顯示器 (Monitor with DP port - shown twice)

可用於家電中的數位電視、DVD 播放機、DVD 錄放影機、視訊轉換器、機頂盒及 PC 監視器的數位視聽裝置。

# DP 线材结构

## 1. 线材蓝图

![线材蓝图技术图纸，显示了完整的线材设计规格和连接器细节]

### 成品示意图
图纸显示了完整的DP线材结构，包括两端的连接器P1和P2，以及中间的线缆部分。

### 注意事项
NOTE:
1. P1,P2端連接頭-黃銅+轉包膠+銅包鐵
2. 測試參數：
   - 電壓：DC 300V AC100V
   - 絕緣阻抗：10M ohm MIN
   - 導通阻抗：2 ohm MAX
   - 適用TDP 1.2/1.4
   - P1=P2=12.2g
3. 文字標印背序尺寸及CRR尺寸
4. Cable=100+/-5ohm (Tr=130ps 20%-80%)
   DP connector=100+/-10ohm (Tr=130ps 20%-80%)

### 線位表
顯示了詳細的線路連接圖，包含各線位的顏色編碼和連接方式。

### 材料表
列出了製造該線材所需的各種材料和規格。

### 標題欄
- RoHS 2.0 Compliant
- 無鹵素認證
- 圖號：DB8429

**觀察線材成品藍圖，線材是由半成品的線纜和連接器組裝而成。**

# 2. 半成品線圖示

![線材實物圖](image1) → ![DP 線材結構圖](image2)

線材結構　DP High-bit-rate 線材常規結構：
　　　　5Twinax signal wires+4C single insulated wires. 為了減少電磁干扰（EMI），標準推薦采取以下措施：
　　1. 采用鋁箔麥拉＋編織雙層屏蔽；
　　2. 鋁箔重疊率达到 20% 以上，編織遮蔽率达到 75% 以上；

![Cable Cross-Section Diagram](image)

**外被：** 主要的材料為 PVC、PE、PP、TPE 還有試樣無鹵等。

**編織：** 在線材外面編上一層鋁鎂絲，以起到屏蔽的作用。
編織的錠數分為 16 錠和 24 錠。

**鋁箔：** 由 AL 和聚酯薄膜粘合而成。

**芯線：** 鍍錫銅絞線、FPE 料、HDPE 以及無鹵色母。

**地線：** 多股鍍錫銅線合而成

# 3. 連接頭圖示

[Image shows a connector cable with arrows pointing to different components]

塑殼：PVC

連接頭：由連接器、鐵殼、卡勾組成

![USB connector diagram with Chinese specifications]

**铁壳：**
SPCC （HV105~130)T=0.30±0.01 电镀

**卡勾：** SUS301(HV370~430)
T=0.40±0.01

**连接头：由后盖、胶芯、壳体、端子组成**

![JH J-HAW Logo]

后盖：LCP（黑色）

锡：无铅环保锡丝

壳体：SPCC T=0.30±0.02 镀镍

胶芯：LCP（黑色）

端子：磷氧铜

# 4. PIN 角定義

## DisplayPort Standard Cable

| Source Side Plug | | Cable Wiring | | Sink Side Plug |
|---|---|---|---|---|
| **At SOURCE** | | | | **At SINK** |
| Signal Type | Pin# | | Pin# | Signal Type |
| Out | ML_Lane 0(p) | 1 | 1 | ML_Lane 3(n) | In |
| GND | GND | 2 | 2 | GND | GND |
| Out | ML_Lane 0(n) | 3 | 3 | ML_Lane 3(p) | In |
| Out | ML_Lane 1(p) | 4 | 4 | ML_Lane 2(n) | In |
| GND | GND | 5 | 5 | GND | GND |
| Out | ML_Lane 1(n) | 6 | 6 | ML_Lane 2(p) | In |
| Out | ML_Lane 2(p) | 7 | 7 | ML_Lane 1(n) | In |
| GND | GND | 8 | 8 | GND | GND |
| Out | ML_Lane 2(n) | 9 | 9 | ML_Lane 1(p) | In |
| Out | ML_Lane 3(p) | 10 | 10 | ML_Lane 0(n) | In |
| GND | GND | 11 | 11 | GND | GND |
| Out | ML_Lane 3(n) | 12 | 12 | ML_Lane 0(p) | In |
| CONFIG | CONFIG1 | 13 | 13 | CONFIG1 | CONFIG |
| CONFIG | CONFIG2 | 14 | 14 | CONFIG2 | CONFIG |
| IO | AUX_CH(p) | 15 | 15 | AUX_CH(p) | IO |
| GND | GND | 16 | 16 | GND | GND |
| IO | AUX_CH(n) | 17 | 17 | AUX_CH(n) | IO |
| In | Hot Plug Detect | 18 | 18 | Hot Plug Detect | Out |
| | Return_DP_PWR | 19 | 19 | Return_DP_PWR | |
| | DP_PWR | 20 | 20 | DP_PWR | |

[The image also contains a technical diagram of a DisplayPort connector on the left side and the JH logo in the top right corner]

# 5.HDMI 与 DP 区别

HDMI 和 DP 的区别在于单位时间内传输图像的帧数，HDMI 最高只能传递 30 帧，而 DP 是没有限制的。

高清晰度多媒体接口（英文：High Definition Multimedia Interface，HDMI）是一种数字化视频/音频接口技术，是适合影像传输的专用型数字化接口，其可同时传送音频和影像信号，最高数据传输速度为 4.5GB/s。

Dp 接口，即 DisplayPort 接口，一种高清晰音视频流的传输接口。最长外接距离都可以达到 15 米，虽然这个距离比 HDMI 要逊色一些，不过接头和接线的相关规格已为日后升级做好了准备，即便未来 DisplayPort 采用新的 2X 速率标准（21.6Gbps），接头和接线也不必重新进行设计。除实现设备与设备之间的连接                                                                                                                                      的接口，甚至是芯片与芯片之间的数据

[THIS IS FIGURE: Image showing two connector types - appears to be HDMI and DisplayPort connectors side by side]

# TYPE-C 線材簡介

2015 年 CES 大展上，Intel 聯合 USB 實施者論壇向公眾展示了 USB 3.1 的威力，具體搭配的接口是 USB Type C，能夠正反隨便插，大小也與 Micro-USB 相差無幾。理論上，USB 3.1 Type C 的傳輸速度能夠達到 10Gbps。Type-C 是 USB 接口的一種連接介面，不分正反兩面均可插入，大小約為 8.3mm×2.5mm，和其他介面一樣支持 USB 標準的充電、數據傳輸、顯示輸出等功能。

# TYPE-C 應用

![MacBook and laptop devices shown at top]

MacBook                    筆記本

![Five different USB-C cable types shown with their connectors]

USB 3.1 A母    Micro-USB    Mini B (5 Pin)    USB 2.0 B公    USB 3.1 B公

![Six different devices/accessories shown below the cables]

U盤           鍵盤          鼠標          手機          MP3          打印機

適用於主機端，用以連接 U 盤、鼠標、鍵盤、硬盤連接線等。

# TYPE-C 组成

## 1. 线材蓝图

| NET_WEIGHT |  |  |  | REV. | ECN NO. | DATE | CHECKED BY | DESCRIPTION |
|------------|--|--|--|-----|---------|------|------------|-------------|
|            |  |  |  | A   |         | 2024/7/8 | Liuhaiyan | FIRST DESIGN |
|            |  |  |  | B   | HD-146065 | 2024/10/25 | 刘海燕 | 变更线工艺/标定工具内容 |

**成品示意图**

[Technical drawing showing cable assembly with two connectors labeled P1 and P2, with dimensions and specifications]

**注意事项**
1. 100% OPEN SHORT TEST
2. 温度老化:
   - 老化温度: ±2mm MAX
3. V conn. IN 为机械介面设计
4. 上焊设温度测试
5. TJ=4J5
6. 输出压力60N以上
7. Support D2F A1/7 Mode OHRC1

**线位表**

WIRE DIAGRAM
P1 | Signal type | Signal type | P2
A2 | TX1- | RX1- | B1
A3 | TX1+ | RX1+ | B10
B11 | RX1+ | TX1+ | A2
B10 | RX1+ | TX1- | A3
B2 | TX2+ | RX2+ | A10
B3 | TX2- | RX2- | A11
A11 | RX2+ | TX2+ | B2
A10 | RX2- | TX2- | B3
Vcc | GND | GND | Vcc
SBU1 | VBUS | VBUS | SBU1
A5 | CC | D- | A5

B5 | Vconn | CC | Vconn | B5

A6 | D+ | D+ | A6
A7 | D- | D- | A7
A8 | SBU1 | SBU2 | B8
B8 | SBU2 | SBU1 | A8
B4 | Shield | Shield | Shield

生产日期编码表:
1st Character Year Codes
[Table showing year codes for 2019-2026]

2nd Character Month codes
[Table showing month codes A-L for months 1-12]

3rd Character Day Codes
[Calendar grid showing day codes 1-31]

**材料表**

Items | Rosa Type C cable规格
Emark TYPE | -
Emark IC Package | VL152 QFN 8
Voltage Drop | between(47cm & 220cm)
Insertion Force | 5-20N
Extraction Force | 3-10N
cycles rating 6-20N

4-Axis Continuity | 97-180° 2N
                   90°-270°-20N
                   97-180°-30N
Wavelength strength | 90°-270°-50N

Cable Fixing | 30Gm cycles for 4 axials
Cable Pull Out | 80 N minimum

**标题栏**

[Company information and drawing details including drawing number E000238]

# 2. 半成品線圖示

[Left side shows a photograph of cable cross-section with label "線材實物圖"]

[Green arrow pointing from photograph to technical diagram]

TYPE-C 3.1 線材結構圖

[Technical circular cross-section diagram showing cable structure with following labels arranged around the circle:]

外殼
鋁箔
11( Component E)
3P( Component A)
7
4P
6
9( Component C)
12( Component D)
8
( Component B)

Inner components labeled:
- 編織
- 套拉
- 套拉
- 編織
- 2P
- 1O
- 鋁箔
- 1P
- 5P

TYPE-C 線纜帶規結構：
30AWG*4P+32AWG*1P+32AWG*4C+24AWG*2C+AB

# Cable Structure Components

![Cable cross-section diagram showing various components with Chinese labels]

**外被**: 主要的材料為 PVC、PE、PP、TPE 還有試樣無菌等。

**編織**: 在線材外面編上一層鋁鎂絲，以起到屏蔽的作用。編織的錠數分為 16 錠和 24 錠。

**鋁箔**: 由 AL 和聚酯薄膜粘合而成。

**麥拉**: 為聚酯薄膜。

**芯線**: 鍍錫銅絞線、FPE 料、HDPE 以及無鹵色母。
**地線**: 多股鍍錫銅線絞合而成

Components labeled in the diagram:
- 芯線 (Core wire)
- 地線 (Ground wire) 
- 外被 (Outer jacket)
- 編織 (Braiding)
- 鋁箔 (Aluminum foil)
- 透明麥拉 (Transparent Mylar)

# 3. 連接頭圖示

![連接頭分解圖，顯示三個主要組件]

**成型外殼**  
材質 PVC/TPE

**鐵殼：材質馬口鐵**

**連接頭：由 PCB 板、鐵殼、卡扣、膠芯和端子組成。**

![JH J-HAW logo]

## PCB 板

![PCB board component image]

### 鐵殼：材質馬口鐵
![Metal shell component image]

### 膠芯：材質 LCP （黑色）
![Black LCP plastic core component image]

### 卡扣：材質馬口鐵
![Metal clip component image]

### 錫：無鉛環保錫絲
![Lead-free solder component image]

[The image shows a technical diagram with arrows pointing from a main assembled component on the left to individual component details on the right, with Chinese text labels describing the materials and specifications of each part]

# 4. PIN 角定義

**Figure A-1** Example Passive 3.5 mm to USB Type-C Adapter

[THIS IS FIGURE: Diagram showing a 3.5mm audio jack to USB Type-C adapter with pin configuration diagram]

## Signal Assignments

### Looking into the product receptacle:

| A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 |
|----|----|----|----|----|----|----|----|----|-----|-----|-----|
| GND | TX1+ | TX1- | Vbus | CC1 | D+ | D- | SBU1 | Vbus | RX2- | RX2+ | GND |

| B12 | B11 | B10 | B9 | B8 | B7 | B6 | B5 | B4 | B3 | B2 | B1 |
|-----|-----|-----|----|----|----|----|----|----|----|----|----| 
| GND | RX1+ | RX1- | Vbus | SBU2 | D- | D+ | CC2 | Vbus | TX2- | TX2+ | GND |

### Looking into the cable or product plug:

| A12 | A11 | A10 | A9 | A8 | A7 | A6 | A5 | A4 | A3 | A2 | A1 |
|-----|-----|-----|----|----|----|----|----|----|----|----|----| 
| GND | RX2+ | RX2- | Vbus | SBU1 | D- | D+ | CC | Vbus | TX1- | TX1+ | GND |

| B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | B9 | B10 | B11 | B12 |
|----|----|----|----|----|----|----|----|----|----|-----|-----|
| GND | TX2+ | TX2- | Vbus | VCONN |  |  | SBU2 | Vbus | RX1- | RX1+ | GND |

# USB2.0 简介

USB （Universal Serial Bus2.0，通用串行总线）是一种应用在计算机领域的新型接口技术。USB 接口具有传输速度更快，支持热插拔以及连接多个设备的特点。目前已经在各类外部设备中广泛的被采用。理论上而USB2.0 则可以达到速度 480Mbps。这几年，随着大量支持 USB 的个人电脑的普及，USB 逐步成为个人电脑的标准接口已经是大势所趋。在主机端，最新推出的个人电脑几乎 100% 支持USB；而在外设端，使用 USB 接口的设备也与日俱增。

[THIS IS FIGURE: Image of a black USB cable with connectors on both ends, coiled in the middle]

# USB2.0 應用

![USB application diagram showing various devices connected via USB2.0, including keyboard, scanner, mobile devices, mouse, and external DVD drive, with a USB cable connector shown at the top]

目前主机端，最新推出的个人电脑几乎 100% 支持 USB；而在外设端，使用 USB2.0 接口的设备也与日俱增，例如数码相机、扫描仪、游戏杆、磁带和软驱、图像设备、打印机、键盘、鼠标等等。

# USB2.0 組成

## 1. 線材藍圖

| REV. | ECN NO. | DATE | CHECKED BY | DESCRIPTION |
|------|---------|------|------------|-------------|
| A    |         | 2018/11/16 | Aaron | NEW DESIGN |

### 成品示意圖
[Technical drawing showing USB connector assembly with dimensions]

Key dimensions shown:
- ∇1000±30
- 42.5±0.5
- 35.5±0.5
- 11.75±0.6/-0∇
- 6.8 MIN
- 8±0.3 (multiple locations)
- 10±0.3
- 31±0.5
- 19±0.5

Components labeled:
- 1, 4, 5 (connector parts)
- ②③④ and ⑤④③ (pin configurations)

### 線位表

**PIN Define**
| CIRCUIT DIAGRAM |
|-----------------|
| P1 - RED - VCC - P2 |
| P3 - WHITE - D+ - P4 |
| P4 - GREEN - D- - P3 |
| P1 - BLACK - GND - P2 |

Shell ——— BRAIDED ——— Shell

### 注意事項

**NOTE:**
1. 内芯線編織組線 & 線殼
2. 鍍層：DC 300V/10ms
3. 絕緣阻抗：20M ohm MIN
4. 導通阻抗：1.5 ohm MAX
5. 適用於USB 2.0標準介面
6. ∇為產品配件尺寸及CPA尺寸

### 材料表

| 序號 | ITEM | PART | DESCRIPTION | QTY |
|------|------|------|-------------|-----|
| ① | OM HOUSING | USB2.0 MINI B(4) CG/金屬殼 shell head sheet | 1 | PCS |
| ② | OVERMOLD | Pin CLEAR | - | g |
| ③ | OVERMOLD | 成型膠料COLOR FR BLACK | - | g |
| ④ | USB A CONN | USB A TYPE 2.0(4線芯)中間焊片 gold head sheet | 1 | 組 |
|   |           | 2core|shielding wire OD5.5MM BLACK 16/18G | 1 | PCS |

**ITEM PART DESCRIPTION**

**CUSTOMER P/N:** ——

**TOLERANCE:**
±-10 ±1
±1-300 ±5
±301-400 ±5
±401mm ±5
ANGLES ±2

**無紅磷**

**RoHS 2.0 Compliant**

**標題欄**

JH P/N: P110180132
CUSTOMER: GDIAS
MODEL:
TITLE: USB2.0 AM TO MINI BM 1M
APPROVED: 
CHECKED: Bobo
DRAWN: Aaron

REV: A
SHEET: 1/2
DRAWN NO: DB7325

SCALE: [?] UNIT: MM

JH-HAW INDUSTRIAL CO.
JH-HAW INDUSTRIAL CO., LTD.
JH-HAW ELECTRONICS CO., LTD.

# 2. 半成品線圖示

## 線材實物圖

[Image showing a cross-section of a damaged cable with colored wires visible]

## USB 2.0

[Diagram showing USB 2.0 cable cross-section with labeled components:]
- 被覆 (component B)
- 鋁織鋁箔 (outer shielding)
- 1P(component A) (signal wires)
- 3 (power wire)
- 地線 (ground wire)

## 高速 USB 線纜常規結構：
1 Twinax UTP signal wire+2C Power wires.

![Cable cross-section diagram with labeled components in Chinese]

**外被**: 主要的材料為 PVC、PE、PP、TPE 還有試樣無鹵等。

**編織**: 在線材外面編上一層鋁鎂絲，以起到屏蔽的作用。
編織的錠數分為 16 錠和 24 錠。

**鋁箔**: 由 AL 和聚酯薄膜粘合而成。

**芯線**: 鍍錫銅絞線、FPE 料、HDPE 以及無鹵色母。
**地線**: 多股鍍錫銅線絞合而成

# 3. 連接頭圖示

![USB connector diagram showing various components with arrows pointing to detailed images]

**成型外模材質 PVC/TPE**

**鐵殼：馬口鐵**

**端子：C2680 鍍金**

**膠芯：PBT**

**端子：C2680 鍍錫**

**鐵殼：馬口鐵**

**連接頭：由卡勾、端子、膠芯、鐵殼組成**

![JH J-HAW logo in top right corner]

[Image shows a technical diagram with three photographs of what appears to be electronic connectors or card slots, with Chinese labels and arrows pointing to different components:]

端子：C2680 镀金

端子：C2680 镀锡

卡勾：马口铁

胶芯：PBT

铁壳：马口铁

# 4.PIN 角定义

![USB connectors diagram showing pin assignments]

**标准USB接口**
- 黑线 绿线 白线 红线

**手机的Micro USB接口**
- 黑线 空端 绿线 白线 红线
- GND  ID   D+   D-   VBUS

# USB3.0 简介

USB3.0 —— 也被认为是 SuperSpeedUSB —— 为那些与 PC 或音频/高频设备相连接的各种设备提供了一个标准接口。计算机只有安装 USB3.0 相关的硬件设备后才可以使用 USB3.0 相关的功能，从键盘到高容吐量磁盘驱动器，各种器件都能够采用这种低成本接口进行平稳运行的即插即用连接，用户基本不用花太多心思在上面。新的 USB 3.0 在保持与 USB 2.0 的兼容性的同时，还极大提高了传输速度，速度高达 5Gbps。并且可以实现了更好的电源管理，能够使主机为器件提供更多的功率，从而实现 USB——充电电池、LED 照明和迷你风扇等应用。可以让主机更快地识别器件提高数据处理的效率。

[Image shows a USB 3.0 cable with two connectors - appears to be USB-A to USB-B style connectors in black]

# USB3.0 應用

![USB 3.0 Application Diagram showing various devices connected via USB 3.0 cables - including printers, scanners, and other peripherals arranged around a central USB 3.0 cable illustration]

USB 3.0 具有后向兼容标准，并兼具传统 USB 技术的易用性和即插即用功能，而 USB 3.0 数据线适用于电脑及其具备 USB 接口的周边产品。如打印机，摄像机，传真机，扫描仪，U盘，MP3，MP4等之间的数据传输。

# USB3.0 组成

## 1. 线材蓝

| NET WEIGHT |  |  |  | REV. | ECN NO. | DATE | CHECKED BY | DESCRIPTION |
|-------------|--|--|--|-----|---------|------|------------|-------------|
|             |  |  |  | A   |         | 2018/03/14 | Jerry | FIRST DESIGN |
|             |  |  |  | B   | JIF-18097 | 2018/09/13 | Jerry | 修改为USB30PIN线路图 |
|             |  |  |  | C   | JHT-24008S | 2022/10/23 | 刘培杰 | 变更线上标记尺寸内容 |

### 成品示意图

[THIS IS FIGURE: Technical drawing showing USB 3.0 cable assembly with connectors P1 and P2, including dimensional specifications and cable routing diagram]

### 注意事项

NOTE:
1. P1、P2端编码后端+螺纹+環L型鋼管+螺纹件
2. 测试参数：
   电    阻：DC 300V  AC 300V
   绝缘電阻：10M ohm MIN
   導通阻抗：≤ 2 ohm MAX
3. 单连：P1 PLUG重量：11.3g  P2 PLUG重量：13.6g
4. 本作成阻抗：90±7 ohm
5. 适用于USB 3.0使用介面
6. ∇ 为滴雨符號尺寸友CPK尺寸     Label
7.    PIN Defin

### 规位表

[THIS IS TABLE: Pin configuration table showing circuit diagram with wire connections and specifications]

### 材料表

[THIS IS TABLE: Materials list showing various components including cable specifications, connectors, and other parts with quantities and descriptions]

PN8IN-CA20-BSE
USB Type-A to Type-B 6Gbps
Cable type: USB Type-A to Type-B 6Gbps

**无铅磷**

**RoHS 2.0 Compliant**

---

Drawing details:
- Drawing number: E000251
- Scale: 1/5
- Sheet: 1/5
- Date: Various revision dates
- Approved by: 朱继杰
- Checked by: 刘培杰

# 2. 半成品線圖示

## 線材實物圖
[Image shows a cross-section of a cable with multiple colored wires visible]

## USB 3.0 線材結構圖
[Diagram shows the cross-sectional structure of a USB 3.0 cable with labeled components:]

- 外被
- 鋁箔
- 編織
- 4 → 3C(Component B)
- 5C(Component C)
- 麥拉鋁箔
- 2P 地線 → 1C(Component A)
- 棉線*4

## 超高速 USB 線纜常規結構：
1 Twinax UTP signal wire+2 Twinax SDP signal wires+2C single wires.

# Cable Structure Components

![Cable cross-section showing various components with Chinese labels and arrows pointing to different parts]

**外被**: 主要的材料為 PVC、PE、PP 還有試樣無鹵等。

**編織**: 在線材外面編上一層鋁鎂絲，以起到屏蔽的作用。
編織的錠數分為 16 錠和 24 錠。

**鋁箔**: 由 AL 和聚酯薄膜粘合而成。

**芯線**: 鍍錫銅絞線、FPE 料、HDPE 以及無鹵色母。

**地線**: 多股鍍錫銅線絞合而成
**棉繩**: 又多股棉線絞和而成。

---

**Component Labels in Image:**
- 棉繩 (Cotton rope)
- 鋁箔 (Aluminum foil) 
- 外被 (Outer jacket)
- 編織 (Braiding)
- 芯線 (Core wire)
- 地線 (Ground wire)

# 3. 連接頭圖示

![Connector diagram showing USB cable components with arrows pointing to different parts]

**成型外模材質 PVC**

**連接器** (pointing to blue connector component)

**鐵殼：馬口鐵** (pointing to metallic connector housing in top right)

**連接器** (pointing to blue connector components in middle right)

**鐵殼：馬口鐵** (pointing to metallic connector components in bottom right)

![JH JHAW logo in top right corner]

![Blue electronic connector components with detailed callouts showing:]

端子: C2680 镀锡

胶芯: PBT (蓝色)

端子: C2680 镀金

![Lower blue connector component with callouts showing:]

端子: C2680 镀锡

胶芯: PBT (蓝色)

端子: C2680 镀金

# 4.USB2.0 与 USB3.0 比较

USB 3.0 在保持与 USB 2.0 的兼容性的同时，还提供了下面的几项增强功能：

极大提高了带宽——高达 5Gbps 全双工（USB2.0 则为 480Mbps 半双工）

USB 3.0 可以在存储器件所限定的存储速率下传输大容量文件（如 HD 电影）。例如，一个采用 USB 3.0 的闪存驱动器可以在 3.3 秒钟将 1GB 的数据转移到一个主机，而 USB 2.0 则需要 33 秒。

受到消费类电子器件不断增加的分辨率和存储性能需求的推动，希望通过宽带互联网连接能够实现更宽的媒体应用，因此，用户需要更快速的传输性能，以简化下载、存储以及对于多媒体的大量内容的共享。USB 3.0 在为消费者提供其所需的简易连接性方面起到了至关重要的作用。

当用于消费类器件时，USB 3.0 将解决 USB 2.0 无法识别无电池器件的问题。主机能够通过 USB 3.0 缓慢降低电流，从而识别这些器件，如电池已经不掉的手机。

![USB connector comparison image showing two USB connectors side by side]

# AUDIO 简介

随着计算机技术的发展，特别是海量存储设备和大容量内存在PC机上的实现，对音频媒体进行数字化处理便成为可能。数字化处理的核心是对音频信息的采样，通过对采集到的样本进行加工，达成各种效果，这是音频媒体数字化处理的基本含义。而AUDIO音频线将经过数字化处理的音频信息传输到音箱、耳机等外部设备中，将声音传播出去。

![Audio cable connector image showing green audio connectors]

# AUDIO 应用

![Audio connection diagram showing various devices connected via 3.5mm audio cable]

**设备连接图:**
- 手机 (Mobile phone)
- 电脑 (Computer) 
- MP3
- 电视 (TV)
- DVD
- 音响 (Speakers)

**连接线:** 3.5mm公公音频线 (3.5mm male to male audio cable)
- 3.5A头 (3.5mm connector) ←→ 3.5A头 (3.5mm connector)

适用于电脑，手机电视机，DVD，MP3 设备与音箱，功放的设备之间的音频信号传输，同时适用于车载 AUX 连接。

# AUDIO 組成

## 1. 線材藍

| REV. | ECN NO. | DATE | CHECKED BY | DESCRIPTION |
|-------|---------|------|------------|-------------|
| 01 |  | 2017-07-07 | Phyllis | NEW DESIGN |

### 成品示意圖

**1850±50**

P1 ←→ P2

**14±0.3** | **32.5±0.3** | **6.5±0.3** | **32.5±0.3** | **14±0.3**

### 連接器規格
- P1, P2: 3芯連接器
- 線材長度: 1850±50mm
- 連接器尺寸詳細標註

### 無紅磷
### RoHS 2.0 Compliant

## 材料表

| 序 | 料號或料名 | 規 格 | 數 |
|----|-----------|-------|-----|
| 3 | 端子線材 | 3芯 PITCH BLACK | 10 | 支 |
| 1 | 線材 | 1.5MM² 300V/50°C 3芯 黑色 PVC材質 RoHS | 5 | - |

**ITEM** | **PART** | **DESCRIPTION** | **Q'TY** | **UNIT**
CUSTOMER P/N:

## 測位表

| PIN | WIRE COLOR | PIN |
|-----|------------|-----|
| 1 | RED | 1 |
| 2 | WHITE | 2 |
| 3 | GND | 3 |

## 注意事項

**TEST REQUEST**
1. OPEN SHORT 100%
2. CT≤2Ω IS≥10MΩ DC 300V
3. HI-V AC 300V 2mA 0.1s
4. 外觀按圖面標示 下彎

**WIRE CONNECTION**

**TOLERANCE:** | **JH P/N:** P121P170005
±1~±0.3 | **CUSTOMER:** CEI045
±1~±20±3 | **MODEL:**
±0.1~±0±5 |
±0.01~±0.1 |

**APPROVED:** Henry | **SHEET:** 1/2
**CHECKED:** Phyllis | **DRAWING NO.:** DB6941
**DRAWN:** Yangtao

# 2. 半成品線圖示

## 線材實物圖

[左側顯示一張線材橫截面的實物照片，可以看到兩根不同顏色的導線（一根紅色，一根白色）被包覆在外層絕緣材料中]

## AUDIO 線材結構圖

[右側顯示線材的結構示意圖，為圓形橫截面圖，標示以下部分：]

- 被覆
- 1 ——————————— 2(component A)
- 纏繞

[圖中顯示兩個圓形導體並排放置在圓形外殼內，周圍有纏繞結構和外層被覆]

# 3. 連接頭圖示

![Connection diagram showing a cable with connector. The left image shows a black cable with a connector end, with an arrow pointing to text that reads "成型外模 材質 PVC" (Molded outer shell, Material: PVC). The right image shows a detailed view of the metal connector plug, with text below reading "連接器" (Connector).]