# enecess Home Assistant 集成

[English](README.md) • [Deutsch](README.de.md) • [Français](README.fr.md) • [Polski](README.pl.md) • [Italiano](README.it.md)

本仓库提供 **enecess** 品牌产品的 Home Assistant（简称 HA）自定义集成。

> **Home Assistant 版本要求：2025.9.0 或更高版本。**

## 当前支持的设备

- **ecoMain**：支持本地 Modbus TCP（自动发现或手动添加）和 enecess 云端连接。
- **ecoSolarMonitor**：仅支持本地，通过所属 ecoMain 的子设备列表添加。
- **ecoPlug**：仅支持 enecess 云端。同一账号可选择多个插座，添加后可在**配置**中调整。

ecoMain 本地功能与固件版本：

- **136–138**：有功功率、正向/反向有功电能。
- **139 及以上**：增加其余九类测量；139 使用**通道相位**设置。
- **140 及以上**：支持 ecoSolarMonitor、**通道配置**和光伏安装设置。

低于 136 的固件不支持本地连接，请使用官方工具更新。ecoSub 或 ecoSolarMonitor 离线时，其传感器显示不可用，其他设备继续更新；原有选择会保留。更新固件后，请重新加载集成。

---

## 通过 HACS 安装

本集成已收录到 **HACS 默认仓库列表**，可直接在 HACS 中搜索 **enecess** 安装。

### 1）安装 HACS（如果你还没有安装）

请先参考 HACS 官方文档完成安装和基础配置：

- **开始使用 HACS**
  [👉点击前往](https://hacs.xyz/docs/use/)

### 2）在 HACS 中下载 / 安装集成

1. 在 Home Assistant 中打开 **HACS**。
2. 搜索 **enecess**，并打开集成详情。
3. 点击 **Download** 下载。
4. 下载完成后，**重启 Home Assistant**：
   - 设置 → 系统 → 重启

> **流程截图：**
> ![HACS integration download 1](docs/images/hacs-integration-download-1.png)

---

> ![HACS integration download 2](docs/images/hacs-integration-download-2.png)

---

> ![HA restart](docs/images/ha-restart.png)

---

## 在 Home Assistant 中添加集成

页面中的**操作**提供**下一步**、**保存**、**返回上一步**或**取消**。选择操作后提交表单；在菜单中用**下一步操作**选择功能，最后选择**完成**保存配置。

ecoMain 的配置流程有 **两种入口**：

### 方式一：从“已发现”入口（zeroconf / mDNS 自动发现）

本集成支持 **zeroconf（mDNS）扫描**。
当 ecoMain 上电并与 Home Assistant 处于同一网络时：

1. 进入 **设置 → 设备与服务**。
2. 在页面上部的 **已发现（Discovered）** 区域，应该能看到 **enecess / ecoMain** 设备卡片。
3. 点击该卡片上的 **添加（Add）**。
4. 集成会自动启动配置流程，使用 **自动发现（本地）** 模式，并自动填好发现到的序列号和 IP 地址。
5. 按照下文“自动发现（本地）”继续选择设备和测量。

> **流程截图：**
> ![Discovered integration card](docs/images/ha-add-integration-1.png)

---

> ![发现的 ecoMain 卡片及 Add 按钮](docs/images/ecomain-solar-discovered.jpg)

---

> ![确认本地 ecoMain 信息](docs/images/ecomain-solar-local-confirm.jpg)

### 方式二：从“添加集成”入口（手动启动）

1. 进入 **设置 → 设备与服务（Devices & services）**。
2. 点击 **添加集成（Add Integration）**。
3. 搜索 **enecess**。
4. 选择设备类型：
   - **ecoMain**：继续选择**自动发现（本地）**、**手动设置（本地）**或**账号登录（云端）**。
   - **ecoPlug**：直接进入云端账号登录。

> **流程截图：**
> ![Add integration entry 1](docs/images/ha-add-integration-1.png)

---

> ![Add integration entry 2](docs/images/ha-add-integration-2.png)

---

> ![Add integration entry 3](docs/images/ha-add-integration-3.png)

---

> ![Select device type](docs/images/select-device-type.png)

---

> ![Select add method](docs/images/select-add-method.png)

---

## ecoMain 支持的添加方式与详细流程

ecoMain 目前支持三种添加方式：

1. **自动发现（本地）**
   - 入口：
     - “添加集成” → enecess → ecoMain → 选择：*自动发现（本地）*
     - 或从设备与服务页面点击 **已发现的 ecoMain 卡片**
2. **手动设置（本地）**
3. **账号登录（云端）**

---

### A）自动发现（本地）

适用于 ecoMain 与 Home Assistant 处于同一局域网，且网络允许 mDNS 发现的情况。

1. 从 **添加集成 → enecess → ecoMain → 自动发现（本地）** 开始，或点击已发现 ecoMain 卡片上的**添加**。
2. 按序列号和 IP / 主机名选择 ecoMain，并确认设备信息。
3. 在**设备设置 → 选择要添加的从机**中选择需要的 ecoSub 或 **ecoSolarMonitor**；也可不选子设备。
4. 在**测量类型**中，分别从 **ecoSolarMonitor**（已选择时显示）和 **ecoMain / ecoSub** 选择读数，再选择**保存**。
5. 按需配置**额外实体**，例如功率取反、绝对值、总和或平均值；最后选择**完成**。

排错提示：

- 如扫描不到设备，可尝试改用 **手动设置（本地）**。
- 请确保 Home Assistant 与 ecoMain 处于同一网段 / VLAN。
- 部分路由器会隔离多播 / mDNS，需要在路由器中开启相关功能。

> **流程截图：**
> ![Auto discovery scan](docs/images/ecomain-auto-scan.png)

---

> ![Select discovered device](docs/images/ecomain-select-discovered.png)

---

> ![确认本地 ecoMain 信息](docs/images/ecomain-solar-local-confirm.jpg)

---

> ![Setup Device 中已选择 ecoSolarMonitor](docs/images/ecomain-solar-subdevices.jpg)

---

> ![Measurement Types 中的五项默认太阳能读数](docs/images/ecomain-solar-measurements.jpg)

---

> ![九项可选太阳能读数及独立的电表分组](docs/images/ecomain-solar-measurements-daily.jpg)

---

> ![Extra Entities 中已选择 Finish](docs/images/ecomain-solar-finish.jpg)

---

> ![为 ecoMain 与 ecoSolarMonitor 命名并分配区域](docs/images/ecomain-solar-assign.jpg)

---

### B）手动设置（本地）

自动发现失败时可使用此方式。请先从路由器或设备设置中查到 ecoMain 的 **IP / 主机名**，并准备好标签上的**主机序列号**。

步骤：

1. 选择 **ecoMain → 手动设置（本地）**。
2. 输入**主机序列号**和**地址（IP 或主机名）**，确认设备信息。
3. 在**设备设置 → 选择要添加的从机**中选择需要的 ecoSub 或 **ecoSolarMonitor**；也可不选子设备。
4. 在**测量类型**中选择 **ecoSolarMonitor**（已选择时显示）和 **ecoMain / ecoSub** 的读数，再选择**保存**。
5. 按需配置**额外实体**，最后选择**完成**。

排错提示：

- 确认 Home Assistant 能访问到该 IP（同一局域网、无防火墙阻断）。
- Modbus TCP 使用端口 **502**，无需在界面中填写。
- 如果无法连接，请重新确认 IP / 主机名、网线连接及网络权限。

> **流程截图：**
> ![Manual setup input 1](docs/images/ecomain-manual-input-1.png)

---

> ![Manual setup input 2](docs/images/ecomain-manual-input-2.png)

---

> ![确认本地 ecoMain 信息](docs/images/ecomain-solar-local-confirm.jpg)

---

> ![Setup Device 中已选择 ecoSolarMonitor](docs/images/ecomain-solar-subdevices.jpg)

---

> ![Measurement Types 中的五项默认太阳能读数](docs/images/ecomain-solar-measurements.jpg)

---

> ![九项可选太阳能读数及独立的电表分组](docs/images/ecomain-solar-measurements-daily.jpg)

---

> ![Extra Entities 中已选择 Finish](docs/images/ecomain-solar-finish.jpg)

---

> ![为 ecoMain 与 ecoSolarMonitor 命名并分配区域](docs/images/ecomain-solar-assign.jpg)

---

### C）账号登录（云端）

在以下情况使用：

- 希望通过 **enecess 云平台** 读取 ecoMain 数据。
- 你的 ecoMain 已经绑定在 **enecess App 账号**（手机 App）下。

> **重要说明：**
> 这里的云端登录使用的是你在 **enecess 官方 App（Android / iOS）** 上使用的账号和密码。
> 本集成不会为你创建新的账号，请直接使用你在 App 中登录的同一套账户信息。

步骤：

1. 选择 **ecoMain → 账号登录（云端）**，输入 enecess App 的**用户名**和**密码**。
2. 从列表中选择 ecoMain，再选择需要的 ecoSub（可选）。
3. 选择**测量类型**，按需配置**额外实体**，最后选择**完成**。

云端数据约每 **60 秒**更新，本地约每 **5 秒**更新。

> **流程截图：**
> ![Cloud login 1](docs/images/ecomain-cloud-login-1.png)

---

> ![Cloud login 2](docs/images/ecomain-cloud-login-2.png)

---

> ![Select cloud master](docs/images/ecomain-cloud-master-select.png)

---

> ![Select cloud slaves](docs/images/ecomain-cloud-slaves-select.png)

---

> ![Select cloud measurement types](docs/images/ecomain-measurement-types-cloud.png)

---

> ![Extra entities placeholder](docs/images/ecomain-cloud-extra-entities-placeholder.png)

---

> ![Cloud accomplish](docs/images/ecomain-cloud-accomplish.png)

---

## ecoPlug 云端添加流程与实体行为

ecoPlug **仅支持通过 enecess Cloud 添加**。本集成不提供 ecoPlug 本地添加方式，也不为 ecoPlug 提供额外实体配置。

添加步骤：

1. 进入 **设置 → 设备与服务 → 添加集成**，选择 **enecess**。
2. 设备类型选择 **ecoPlug**。
3. 输入 enecess App 云端账号的用户名和密码。
4. 登录成功后，从列表中**多选一个或多个**插座；每个选项都会显示插座名称和序列号。
5. 完成后，同一云端账号会创建一个 ecoPlug 集成条目，其中包含本次选择的全部插座。
6. 后续如需更改选择，进入 **设置 → 设备与服务 → enecess → 配置**，增加或移除插座并保存选项。

> ![Select ecoPlug device type](docs/images/ecoplug-select-device-type.png)

---

> ![ecoPlug cloud login](docs/images/ecoplug-cloud-login.png)

---

> ![Select ecoPlug plugs](docs/images/ecoplug-select.png)

---

> ![ecoPlug setup complete](docs/images/ecoplug-complete.png)

---

> ![Open ecoPlug options](docs/images/ecoplug-options.png)

每个已选择的 ecoPlug 只创建以下实体：

- 一个用于通过云端开关插座的**开关实体**。
- `power_rt`：一个以 **W（瓦）**为单位的有功功率传感器。
- `energy_total`：一个以 **kWh（千瓦时）**为单位的累计电能传感器。

ecoPlug 数据约每 **60 秒**更新。开关操作成功后会立即显示目标状态，后续以云端更新的状态为准。

---

## 配置与调整

### 修改已添加的集成条目

打开 **设置 → 设备与服务 → enecess → 配置**。

- ecoMain 可调整已选择的 ecoSub/ecoSolarMonitor、测量类型、额外实体和本地安装设置。
- ecoPlug 可调整已选择的插座。
- 设备类型、添加方式和 ecoMain 主设备不能直接更改；如需更换，请移除条目后重新添加。

为已有本地条目添加或调整太阳能测量：

1. 在**调整 ecoMain → 选择要添加的从机**中选择 **ecoSolarMonitor** 及需要的 ecoSub，进入**测量类型**。
2. 分别选择 **ecoSolarMonitor** 和 **ecoMain / ecoSub** 的读数，选择**保存**。
3. 按需进入**通道配置**或 **ecoSolarMonitor 配置**；返回菜单后选择**完成**。

> ![Adjust ecoMain 中的太阳能选择与上部操作](docs/images/ecomain-solar-options.jpg)

---

> ![Next Action 中的通道配置与太阳能配置入口](docs/images/ecomain-solar-options-actions.jpg)

### 测量类型

添加设备后选择读数；后续可在**配置 → 调整 ecoMain → 下一步操作 → 测量类型**中修改。

- **ecoSolarMonitor** 和 **ecoMain / ecoSub** 分别选择，两组合计至少保留一项；支持只选择太阳能读数。
- 选择**保存**后，最后在菜单选择**完成**。
- 取消设备或测量前，请先移除依赖它们的额外实体。

以下是 ecoMain / ecoSub 的本地测量选项；太阳能读数另见[太阳能实体清单](#solar-entities)。

| 类别     | 含义                    | 默认启用 |
| ------ | --------------------- | ---- |
| 正向有功电能 | 沿 CT 箭头方向累计的有功电能（Wh）  | 是    |
| 反向有功电能 | 逆 CT 箭头方向累计的有功电能（Wh）  | 是    |
| 正向无功电能 | 正向累计无功电能（varh）        | 否    |
| 反向无功电能 | 反向累计无功电能（varh）        | 否    |
| 视在电能   | 视在电能 (VAh)            | 否    |
| 有功功率   | 实时有功功率（W）             | 是    |
| 无功功率   | 无功功率（var）             | 否    |
| 视在功率   | 视在功率（VA）              | 否    |
| 电压     | 电压（V）                 | 否    |
| 电流     | 电流（A）                 | 否    |
| 功率因数   | 有功功率与视在功率之比，无单位       | 否    |
| 频率     | 电网频率（Hz），仅 ecoMain 提供 | 否    |

各测量适用的相位、合计和通道见下文实体表。云端仅提供**有功功率**和**电能**，默认均选择；ecoPlug 使用固定的开关、功率和电能实体。

### 自定义公式实体

用测量数据创建新传感器，例如两路功率的差值或平均值。

1. 先在**测量类型**中启用需要的读数，再选择**添加公式实体**。
2. 填写名称，选择**结果类型 / 单位**。
3. 在**选择源实体**中选择至少一个来源。来源按测量类型分组，可跨组选择。
4. 按页面显示的 `a`、`b` 等变量填写**表达式**，并检查计算结果的单位。

太阳能功率位于**有功功率 (W)**，累计和昨日/今日电量位于**有功电能（累计量，Wh）**；辐照度、组件温度、倾角和性能比各有分组。选项会显示实际名称和单位，例如 `solar_today_actual_energy (Wh)`。

从来源页继续会清空原表达式，编辑时也需重新填写。没有单位的结果可选择**数值（无单位）**。

> ![Add formula entity](docs/images/ecomain-formula-add.png)

---

> ![Set formula name and result type](docs/images/ecomain-formula-setup.png)

---

> ![Select Source Entities 中以 W 为单位的预估与实际太阳能功率](docs/images/ecomain-solar-formula-sources.jpg)

---

> ![Enter formula expression](docs/images/ecomain-formula-expression.png)

| 公式           | 两路功率的计算结果       |
| ------------ | --------------- |
| `max(a-b,0)` | a 减 b，小于 0 时取 0 |
| `(a+b)/2`    | a 和 b 的平均功率     |

- 支持 `+`、`-`、`*`、`/`、括号及 `abs`、`min`、`max`、`round`。
- 用**编辑公式实体**修改名称、来源或公式；更换结果类型或单位需新建实体。
- 用**移除额外实体**删除公式。取消某类测量前，先删除使用它的公式。
- 数据缺失或无法计算时，结果显示为不可用。

### 安装设置（本地固件 140 及以上）

打开**配置 → 调整 ecoMain**，在**下一步操作**中选择**通道配置**或 **ecoSolarMonitor 配置**。

#### 通道配置

1. 在**设备**中选择 ecoMain 或已选择且在线的 ecoSub。
2. 展开**通道 1**至**通道 10**，设置**相位**（**L1、L2、L3**）和**电流互感器**（**30 A** 或 **100 A**）。
3. ecoMain 的**主回路电流互感器**分区包含 **L1、L2、L3**，均只支持 **100 A**。
4. 选择**保存**，返回菜单后选择**完成**。

> ![Channel Configuration 中已选择 ecoMain](docs/images/ecomain-solar-channel-device.jpg)

---

> ![未保存的 Channel 4 示例：Phase L2 与 30 A、100 A 互感器选项](docs/images/ecomain-solar-channel-settings.jpg)

---

> ![Main Circuit Current Transformers 中的 100 A 选项](docs/images/ecomain-solar-main-transformers.jpg)

#### ecoSolarMonitor 配置

已添加 **ecoSolarMonitor** 后，进入此页面：

1. 填写**光伏总装机容量**，单位 **W**，使用整数。
2. 填写组件的**功率温度系数**，单位 **%/°C**，最多三位小数。
3. 在 **ecoMain、ecoSub 1、ecoSub 2、ecoSub 3** 列表中选择逆变器对应的**通道 1**至**通道 10**。
4. 列表留空会清除该组逆变器通道。
5. 选择**保存**，返回菜单后选择**完成**。

> ![装机容量、温度系数与逆变器通道示例](docs/images/ecomain-solar-configuration.jpg)

> **注意：设备设置保存后立即生效，之后取消配置也不会撤销。**

### 通道相位（本地固件 139）

在**配置 → 下一步操作 → 通道相位**中选择 ecoMain 或已选择且在线的 ecoSub，为十个通道分别选择 **L1、L2、L3**，然后选择**保存**。固件 140 及以上使用上面的**通道配置**。

> ![Open channel phase settings](docs/images/ecomain-phase-options.png)

---

> ![Select device for phase settings](docs/images/ecomain-phase-device.png)

---

> ![Set channel phases](docs/images/ecomain-channel-phases.png)

## 设备命名规则

集成条目创建后，默认标题格式如下：

- **本地模式：** `ecoMain <序列号> (Local)`
- **云端模式：** `ecoMain <序列号> (Cloud)`

示例：

- `ecoMain 12345678 (Local)`
- `ecoMain 12345678 (Cloud)`

---

## 实体命名规则与含义

下表同时列出测量含义和实际 HA 实体名称。自动化中请从 HA 实体页面复制完整的 `sensor.…` 实体 ID。额外实体使用配置时填写的名称，也可在 HA 中重命名。

### 测点与实体名称

ecoMain / ecoSub 的实体名称由下表的测点前缀和测量后缀组成：

| 测点       | 名称前缀                           | 范围                   |
| -------- | ----------------------------- | -------------------- |
| 主机分相     | `main_l1`、`main_l2`、`main_l3` | 仅本地                  |
| 主机三相合计   | `main_all`                    | 本地部分测量及云端            |
| 主机支路     | `main_ch1` … `main_ch10`      | 本地及云端                |
| 已选择的从机支路 | `sub1_ch1` … `sub3_ch10`      | 每台 ecoSub 十路，仅创建所选从机 |

从机没有独立的 L1/L2/L3、三相合计或频率实体。下表的“支路”包含主机十路和每台已选择从机的十路。

### 本地模式（Modbus）完整测量清单

固件 **136–138** 仅支持前三类；固件 **139 及以上**支持全部十二类。默认只选择前三类，其余需在**测量类型**中启用。这里的默认值指测量选项；未选择的测量不会创建传感器。

| 测量名称   | HA 名称后缀 / 完整名称                   | 单位 | 主机分相 | 主机合计 | 支路  | 默认选择    |
| ------ | --------------------------- | ---- | ---- | ---- | --- | ------- |
| 有功功率   | `power_rt`                  | W    | ✓    | ✓    | ✓   | 是       |
| 正向有功电能 | `energy_fwd_total`          | Wh   | ✓    | ✓    | ✓   | 是       |
| 反向有功电能 | `energy_rev_total`          | Wh   | ✓    | ✓    | ✓   | 是       |
| 正向无功电能 | `reactive_energy_fwd_total` | varh | ✓    | ✓    | ✓   | 否       |
| 反向无功电能 | `reactive_energy_rev_total` | varh | ✓    | ✓    | ✓   | 否       |
| 视在电能   | `apparent_energy_total`     | VAh  | ✓    | ✓    | ✓   | 否       |
| 视在功率   | `apparent_power_rt`         | VA   | ✓    | ✓    | ✓   | 否       |
| 无功功率   | `reactive_power_rt`         | var  | ✓    | ✓    | ✓   | 否       |
| 电压     | `voltage_rt`                | V    | ✓    | —    | ✓   | 否       |
| 电流     | `current_rt`                | A    | ✓    | —    | ✓   | 否       |
| 功率因数   | `power_factor_rt`           | 无单位  | ✓    | —    | ✓   | 否       |
| 频率     | `main_frequency_rt`（完整名称）    | Hz   | —    | —    | —   | 否，仅主机一个 |

表中单位为原生单位，HA 可按用户设置转换显示。

示例：`main_l1_power_rt` 是主机 L1 有功功率，`main_all_reactive_power_rt` 是主机三相合计无功功率，`main_ch1_voltage_rt` 是主机通道 1 电压，`sub1_ch1_reactive_energy_fwd_total` 是从机 1 通道 1 正向累计无功电能。

#### 电流互感器（CT）方向

CT 箭头标识正方向。`energy_fwd_total` 记录正向有功电能，`energy_rev_total` 记录反向有功电能；无功电能同样区分正反方向。`_rt` 表示瞬时值，`_total` 表示累计值。

<a id="solar-entities"></a>

### ecoSolarMonitor

ecoSolarMonitor 属于当前 ecoMain，提供以下十四项读数。前五项默认选择，昨日/今日等其他读数可按需启用。

| 测量含义 | HA 实体名称 | 单位 | 默认选择 |
| --- | --- | --- | --- |
| 辐照度 | `solar_irradiance` | W/m² | 是 |
| 倾角 | `solar_tilt_angle` | ° | 是 |
| 组件温度 | `solar_module_temperature` | °C | 是 |
| 实际功率 | `solar_actual_power` | W | 是 |
| 理论功率 | `solar_estimated_power` | W | 是 |
| 性能比 | `solar_performance_ratio` | % | 否 |
| 累计实际电量 | `solar_actual_energy` | Wh | 否 |
| 累计理论电量 | `solar_estimated_energy` | Wh | 否 |
| 昨日性能比 | `solar_yesterday_performance_ratio` | % | 否 |
| 昨日理论电量 | `solar_yesterday_estimated_energy` | Wh | 否 |
| 昨日实际电量 | `solar_yesterday_actual_energy` | Wh | 否 |
| 今日性能比 | `solar_today_performance_ratio` | % | 否 |
| 今日理论电量 | `solar_today_estimated_energy` | Wh | 否 |
| 今日实际电量 | `solar_today_actual_energy` | Wh | 否 |

今日电量每天重新累计；昨日电量和昨日性能比显示前一天的数据。

> ![已启用的全部十四项 ecoSolarMonitor 读数、名称与单位](docs/images/ecomain-solar-entities-all.jpg)

### 云端模式完整测量清单

云端的**有功功率**和**电能**默认均选择，适用于主机合计及所选设备的通道；不提供分相测量。

| 测量选项 | 测量含义 | HA 名称后缀 | 单位 |
| --- | --- | --- | --- |
| 有功功率 | 1 分钟平均有功功率 | `power_avg_1m` | W |
| 电能 | 1 分钟有功电能增量 | `energy_total_1m` | Wh |
| 电能 | 累计有功电能估算值 | `energy_accumulated` | Wh |

例如主机合计为 `main_all_power_avg_1m`、`main_all_energy_total_1m`、`main_all_energy_accumulated`；支路可替换前缀为 `main_ch1` 或 `sub1_ch1`。

能源面板请选择 `energy_accumulated` 对应的累计实体，不要选择 `energy_total_1m` 分钟增量。云端累计值是估算值，断网或重启可能造成误差。

### ecoPlug 实体

每个 ecoPlug 固定提供以下三个云端实体：

| 测量含义 | HA 实体名称 | 单位 |
| --- | --- | --- |
| 插座开关 | 使用插座设备名称 | — |
| 有功功率 | `power_rt` | W |
| 累计有功电能 | `energy_total` | kWh |

ecoPlug 电能单位为 kWh，ecoMain 为 Wh。

### ecoMain 额外实体

额外实体需要手动配置，可用于本地或云端 ecoMain：

| 操作    | 来源与结果                        |
| ----- | ---------------------------- |
| 取反    | 单个有功功率来源，结果为 `-a`            |
| 绝对值   | 单个有功功率来源，结果为 `abs(a)`        |
| 总和    | 多个同类型有功功率或累计有功电能来源，结果为总和     |
| 平均值   | 多个同类型有功功率或累计有功电能来源，结果为平均值    |
| 自定义公式 | 已启用且受支持的测量来源；允许跨类型组合，需自行确认单位 |

公式可选择功率、电能、电压、电流、功率因数、频率或无单位数值等结果类型；请选用与计算结果一致的类型和单位。配置与表达式规则见上文“自定义公式实体”。

---

## 常见问题 / 故障排查

### Q1：ecoMain 没有出现在“已发现（Discovered）”列表中

**可能原因：**

- ecoMain 和 Home Assistant 不在同一网段 / VLAN。
- 路由器或防火墙阻断了多播 / mDNS 流量。

**排查建议：**

1. 确认 ecoMain 与 Home Assistant 在同一网络（同一个子网或 VLAN）。
2. 检查路由器设置，确保多播 / mDNS 被允许在相关接口之间转发。
3. 如仍无法自动发现，可改用 **“手动设置（本地）”**，直接填入 IP 和序列号。

---

### Q2：提示“未找到兼容的设备”

- **本地**：检查 ecoMain 是否上电、接入局域网；自动发现失败时改用**手动设置（本地）**。
- **云端**：检查 ecoMain 是否已绑定到当前 enecess App 账号。

---

### Q3：提示“无法连接到设备”

检查 IP / 主机名、网络连接和防火墙，确认 Home Assistant 能访问设备的 **TCP 502 端口**。设备正在重启时请稍后重试；固件低于 **136** 时，先使用官方工具更新。

---

### Q4：本地配置需要什么固件版本？

最低为 **136**；更多测量和安装功能见开头的固件说明。可通过官方 enecess 工具或 App 更新；不清楚更新方法时，请联系安装服务商或官方支持。

---

### Q5：提示“无法连接到云服务”

检查 Home Assistant 的互联网连接和 DNS。若 enecess 云服务暂时不可用，请稍后重试。

---

### Q6：提示“用户名或密码无效”

请使用 enecess App 的同一账号和密码。先尝试在 App 中登录；如仍失败，请在 App 中找回账号或重置密码，再回到集成中填写。

---

### Q7：提示“该设备已配置”

同一 ecoMain 不能以相同连接方式重复添加。进入**设置 → 设备与服务**找到已有条目，通过**配置**调整；如需更换设备或连接方式，再移除并重新添加。

---

### Q8：添加后还能修改哪些配置？

ecoMain 可调整所选子设备、测量类型、额外实体及本地安装设置；ecoPlug 可调整所选插座。详见上文“配置与调整”。更换设备类型、添加方式或 ecoMain 主设备时，需要重新添加条目。

---

### Q9：更新集成后，原有条目不工作了

先查看对应版本的发布说明并按升级指引处理；如需重新配置，再移除旧条目并重新添加。

---

### Q10：为什么只看到部分从机或部分通道？

检查子设备的供电和接线，并在**配置 → 调整 ecoMain**中选择设备、启用所需**测量类型**，最后选择**完成**。

新添加的子设备需要在线；已选择的设备离线后会保留，传感器显示不可用。取消设备或测量前，先移除依赖的额外实体。

---

### Q11：为什么有的值总是 0，或者出现负值？

- **CT 方向**：检查箭头是否与预期电流方向一致；方向反了可能导致负功率或反向电能增加。
- **没有负载**：设备未用电时，功率和电量变化会接近 0。
- **云端延迟**：云端提供分钟平均功率和分钟电量，变化比本地读数慢。

`*_energy_fwd_total` 表示正向累计电能，`*_energy_rev_total` 表示反向累计电能。

---

### Q12：云端模式下为什么没有 L1/L2/L3 分相实体？

分相测量仅在本地模式提供。云端提供主机合计和通道的分钟平均功率、分钟电量增量及累计电量估算值，名称见上文云端实体表。

---

### Q13：数据多久更新一次？

本地约 **5 秒**，云端约 **60 秒**。云端功率和电量本身按分钟统计，实际变化会较慢。

---

### Q14：云端账号与密码如何保存？

云端登录信息保存在 Home Assistant 的配置中，用于后续连接。请保护好 Home Assistant 和备份；不再需要云端访问时，可移除集成条目。

---

## 支持与反馈

如果你在使用过程中遇到问题，欢迎反馈：

- 尽量附上 Home Assistant 的相关日志。
- 说明你的添加方式（本地自动 / 本地手动 / 云端）。
- 描述你的 ecoMain / ecoSub 型号、安装方式及网络环境。
- 附上界面中的具体错误提示。
