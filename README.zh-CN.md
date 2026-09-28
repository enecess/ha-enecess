# enecess Home Assistant 集成

[English](README.md) • [Deutsch](README.de.md) • [Français](README.fr.md) • [Polski](README.pl.md) • [Italiano](README.it.md)

本仓库提供 **enecess** 品牌产品的 Home Assistant（简称 HA）自定义集成。

## 当前支持的设备

- **ecoMain**
    - 本地：Modbus TCP（支持 zeroconf / mDNS 自动发现）
    - 云端：enecess Cloud（enecess 云服务）
- **ecoPlug**
    - 仅支持云端（enecess Cloud）。
    - 同一云端账号创建一个集成条目，可按名称和序列号多选一个或多个插座。
    - 添加后可通过该条目的**配置 / Options** 修改已选择的插座。

> **固件要求（本地模式）：** 通过 Modbus TCP 在本地添加 ecoMain 时，设备固件版本必须为 **136 或更高版本**。如果固件版本低于 136，或设备未提供兼容的固件版本寄存器，集成会提示 **设备固件版本过低**。云端模式不执行此本地固件校验。

- 本地固件 136–138：支持有功功率、正向/反向有功电能。
- 本地固件 139 及以上：还支持其余八类测量和通道相位设置。
- 旧固件不支持的选项会隐藏。

---

## 通过 HACS 安装

本集成可通过 **HACS** 安装。正式加入 HACS 默认仓库列表后，可直接在 **Integrations** 中搜索 **enecess**。在审核收录期间，请先使用以下任一方式将本仓库添加到 HACS。

### 1）安装 HACS（如果你还没有安装）

请先参考 HACS 官方文档完成安装和基础配置：

- **开始使用 HACS**
  [👉点击前往](https://hacs.xyz/docs/use/)

### 2）在 HACS 审核收录期间添加本仓库

#### 方式 A：一键添加仓库（推荐）

点击下面的按钮，将本仓库添加为 HACS 自定义集成：

- **添加到 HACS（通过 My Home Assistant 重定向）：**
  [👉点击前往](https://my.home-assistant.io/redirect/hacs_repository/?owner=enecess&repository=ha-enecess&category=integration)

> 打开链接后，在新页面中填入你的 **Home Assistant 地址**，按提示完成添加。

> **流程截图：**
> ![Add repository redirect](docs/images/hacs-add-repo-redirect.png)

#### 方式 B：在 HACS 手动添加

1. 打开 Home Assistant。
2. 进入 **HACS**。
3. 右上角菜单 → 选择 **Custom repositories（自定义仓库）**。
4. 在对话框中填入仓库地址（例如：`https://github.com/enecess/ha-enecess`）。
5. Category（类别）选择：**Integration**。
6. 点击 **Add**。

> **流程截图：**
> ![HACS custom repositories 1](docs/images/hacs-custom-repositories-1.png)
---
> ![HACS custom repositories 2](docs/images/hacs-custom-repositories-2.png)

### 3）在 HACS 中下载 / 安装集成

1. 在 HACS 中切换到 **Integrations**。
2. 搜索 **enecess**。
3. 打开后点击 **Download** 下载。
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

- 中间页面可通过**操作**选择**下一步**／**保存**、**返回上一步**或**取消**。
- 返回保留已填内容；有上一页时才显示此选项。
- 添加设备时取消，结束添加；从菜单进入的子操作取消，返回该菜单。
- 在配置首页取消，退出且不保存待提交的更改。

ecoMain 的配置流程有 **两种入口**：

### 方式一：从“已发现”入口（zeroconf / mDNS 自动发现）

本集成支持 **zeroconf（mDNS）扫描**。
当 ecoMain 上电并与 Home Assistant 处于同一网络时：

1. 进入 **设置 → 设备与服务**。
2. 在页面上部的 **已发现（Discovered）** 区域，应该能看到 **enecess / ecoMain** 设备卡片。
3. 点击该卡片上的 **添加（Add）**。
4. 集成会自动启动配置流程，使用 **自动发现（本地）** 模式，并自动填好发现到的序列号和 IP 地址。
5. 接下来按照下文“自动发现（本地）”的步骤完成（选择从机、确认、完成）。

> **流程截图：**
> ![Discovered integration card](docs/images/ha-add-integration-1.png)
---
> ![Discovered configure flow 1](docs/images/ecomain-discovered-configure-1.png)
---
> ![Discovered configure flow 2](docs/images/ecomain-discovered-configure-2.png)

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

推荐在以下场景使用：

- ecoMain 与 Home Assistant 处于同一局域网（同一网段 / VLAN）。
- 网络中 mDNS / Bonjour / zeroconf 功能正常。

该方式有两种启动方式：

- **手动启动**：在“添加集成”时选择 **自动发现（本地）**。
- **已发现启动**：在设备与服务页面点击 **已发现** 区域中的 ecoMain 卡片，进入配置流程。
  此时集成会自动把 zeroconf 中发现到的序列号和 IP 带入后续步骤。

通用步骤如下（两种入口后续流程相同）：

1. 启动 ecoMain 配置：
    - 从 **添加集成 → enecess → ecoMain → 自动发现（本地）**，
    - 或点击 **已发现** 区域中的 ecoMain 卡片上的 **Add**。
2. 集成会通过 **mDNS** 在网络中扫描匹配的服务。
3. 如果找到设备，将显示一个列表，请根据序列号及 IP / 主机名选择你的 ecoMain。
4. 确认设备信息（序列号和地址）。
5. 集成会先读取设备的 **固件版本**，若版本过低会中止并提示；版本符合要求后，会通过 **Modbus TCP** 连接并探测 **在线从机（ecoSub）**。
6. 如果探测到从机，可以勾选需要添加的从机（可选）。
7. 选择**测量类型**，然后可选配置 **额外实体**：
    - 基于功率源实体创建取反或绝对值实体。
    - 选择多个同类型功率 / 能耗源实体，创建总和或平均值实体。
    - 聚合实体会保持源类型的 `device_class`、`state_class` 和原生单位。
8. 完成后，会生成一个集成条目。

排错提示：

- 如扫描不到设备，可尝试改用 **手动设置（本地）**。
- 请确保 Home Assistant 与 ecoMain 处于同一网段 / VLAN。
- 部分路由器会隔离多播 / mDNS，需要在路由器中开启相关功能。

> **流程截图：**
> ![Auto discovery scan](docs/images/ecomain-auto-scan.png)
---
> ![Select discovered device](docs/images/ecomain-select-discovered.png)
---
> ![Confirm local device](docs/images/ecomain-local-confirm.png)
---
> ![Select online slaves](docs/images/ecomain-select-slaves.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **截图待补：测量类型（本地）**
>
> ![截图待补：测量类型（本地）](docs/images/0_default.png)

---
> ![Extra entities placeholder](docs/images/ecomain-extra-entities-placeholder.png)
---
> ![Local accomplish](docs/images/ecomain-local-accomplish.png)

---

### B）手动设置（本地）

在以下情况使用：

- 自动发现无法找到你的 ecoMain。
- 你已经知道 ecoMain 的 IP / 主机名和主机序列号。

准备工作：

- 从路由器 DHCP 列表或者设备网络配置中查到 ecoMain 的 **IP 地址**。
- 准备好 ecoMain 的 **主机序列号**（通常贴在设备标签上）。

步骤：

1. 在添加集成流程中选择：
    - 设备类型：**ecoMain**
    - 添加方式：**手动设置（本地）**
2. 按提示输入：
    - **主机序列号**
    - **地址（IP 或主机名）**
3. 确认设备信息（序列号和 IP）。
4. 集成会先读取 **固件版本**，若版本过低会停止并提示更新固件；版本符合要求后，会通过 **Modbus TCP** 连接并获取 **在线从机（ecoSub）**。
5. 如果探测到从机，可勾选需要添加的从机（可选）。
6. 选择**测量类型**，然后可选配置 **额外实体**：
    - 基于功率源实体创建取反或绝对值实体。
    - 选择多个同类型功率 / 能耗源实体，创建总和或平均值实体。
    - 聚合实体会保持源类型的 `device_class`、`state_class` 和原生单位。
7. 完成后，会生成一个集成条目。

排错提示：

- 确认 Home Assistant 能访问到该 IP（同一局域网、无防火墙阻断）。
- Modbus TCP 使用标准端口 **502**（本集成中固定为 502，前端暂不支持修改）。
- 如果无法连接，请重新确认 IP / 主机名、网线连接及网络权限。

> **流程截图：**
> ![Manual setup input 1](docs/images/ecomain-manual-input-1.png)
---
> ![Manual setup input 2](docs/images/ecomain-manual-input-2.png)
---
> ![Confirm local device](docs/images/ecomain-local-confirm.png)
---
> ![Select online slaves](docs/images/ecomain-select-slaves.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **截图待补：测量类型（本地）**
>
> ![截图待补：测量类型（本地）](docs/images/0_default.png)

---
> ![Extra entities placeholder](docs/images/ecomain-extra-entities-placeholder.png)
---
> ![Local accomplish](docs/images/ecomain-local-accomplish.png)

---

### C）账号登录（云端）

在以下情况使用：

- 希望通过 **enecess 云平台** 读取 ecoMain 数据。
- 你的 ecoMain 已经绑定在 **enecess App 账号**（手机 App）下。

> **重要说明：**
> 这里的云端登录使用的是你在 **enecess 官方 App（Android / iOS）** 上使用的账号和密码。
> 本集成不会为你创建新的账号，请直接使用你在 App 中登录的同一套账户信息。

步骤：

1. 在添加集成流程中选择：
    - 设备类型：**ecoMain**
    - 添加方式：**账号登录（云端）**
2. 输入你的云端账号（即 **enecess App** 的账号）：
    - **用户名**
    - **密码**
3. 集成会调用云端接口登录，并列出账号下所有可用的 ecoMain 主机。
4. 在列表中选择你要添加的 ecoMain 主机。
5. 如果账号下还存在 ecoSub 从机，集成会继续读取并列出，从中勾选需要添加的从机（可选）。
6. 选择**测量类型**，然后可选配置 **额外实体**：
    - 基于功率源实体创建取反或绝对值实体。
    - 选择多个同类型功率 / 能耗源实体，创建总和或平均值实体。
    - 聚合实体会保持源类型的 `device_class`、`state_class` 和原生单位。
7. 完成后，会生成一个云端模式的集成条目。

说明：

- 云端返回的数据是根据远端配置处理后的数据。
- 云端刷新频率通常比本地轮询慢（约 `60s` 一次，本地约为 `5s` 一次）。

> **流程截图：**
> ![Cloud login 1](docs/images/ecomain-cloud-login-1.png)
---
> ![Cloud login 2](docs/images/ecomain-cloud-login-2.png)
---
> ![Select cloud master](docs/images/ecomain-cloud-master-select.png)
---
> ![Select cloud slaves](docs/images/ecomain-cloud-slaves-select.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-cloud.png -->

> **截图待补：测量类型（云端）**
>
> ![截图待补：测量类型（云端）](docs/images/0_default.png)

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

<!-- Screenshot pending: docs/images/ecoplug-cloud-login.png -->

> **截图待补：ecoPlug 云端登录**
>
> ![截图待补：ecoPlug 云端登录](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-select.png -->

> **截图待补：选择 ecoPlug 插座**
>
> ![截图待补：选择 ecoPlug 插座](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-complete.png -->

> **截图待补：ecoPlug 添加完成**
>
> ![截图待补：ecoPlug 添加完成](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecoplug-options.png -->

> **截图待补：修改已选的 ecoPlug 插座**
>
> ![截图待补：修改已选的 ecoPlug 插座](docs/images/0_default.png)

每个已选择的 ecoPlug 只创建以下实体：

- 一个用于通过云端开关插座的**开关实体**。
- `power_rt`：一个以 **W（瓦）**为单位的实时功率传感器。
- `energy_total`：一个以 **kWh（千瓦时）**为单位的累计电能传感器。

集成大约每 **60 秒**从云端轮询一次 ecoPlug 数据。控制请求成功后，开关状态会立即更新为云端已接受的目标状态；后续云端轮询仍是权威状态来源，如果插座或云端返回不同状态，轮询结果会进行修正。

---

## 配置与调整

- 中间页面可通过**操作**选择**下一步**／**保存**、**返回上一步**或**取消**。
- 返回保留已填内容；有上一页时才显示此选项。
- 添加设备时取消，结束添加；从菜单进入的子操作取消，返回该菜单。
- 在配置首页取消，退出且不保存待提交的更改。

### 修改已添加的集成条目

进入 **设置 → 设备与服务 → enecess → 配置**，可以调整可变选项。

可以修改：

- ecoMain 条目：已选择的 ecoSub 从机、测量类型、额外实体配置及本地通道相位。
- ecoPlug 账号条目：已选择的插座。

不可修改：

- 设备类型。
- 添加方式。
- ecoMain 条目中已选择的主设备 / 序列号。

> **流程截图：**
> ![Options placeholder](docs/images/ecomain-options-placeholder-1.png)
> ![Options placeholder](docs/images/ecomain-options-placeholder-2.png)
> ![Options placeholder](docs/images/ecomain-options-placeholder-3.png)

如需修改不可变配置：

1. 进入 **设置 → 设备与服务**。
2. 找到 **enecess** 对应的 ecoMain 条目。
3. 删除该集成条目。
4. 根据新的需求，重新添加一次集成。

### 测量类型

- 添加 ecoMain 时，在选择 ecoSub 后、配置额外实体前选择**测量类型**。
- 之后可在条目的**配置**页面将下一步操作设为**测量类型**，再次调整。
- 必须至少选择一项；若额外实体正在引用某类测量，需先移除相应额外实体，才能取消该测量类型。

<!-- Screenshot pending: docs/images/ecomain-measurement-types-local.png -->

> **截图待补：测量类型（本地）**
>
> ![截图待补：测量类型（本地）](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-measurement-types-cloud.png -->

> **截图待补：测量类型（云端）**
>
> ![截图待补：测量类型（云端）](docs/images/0_default.png)

本地固件 139 及以上提供以下十一类测量；固件 136–138 仅支持前三类：

| 类别 | 含义 | 默认启用 |
| --- | --- | --- |
| 有功功率 | 实时有功功率（W） | 是 |
| 正向有功电能 | 沿 CT 箭头方向累计的有功电能（Wh） | 是 |
| 反向有功电能 | 逆 CT 箭头方向累计的有功电能（Wh） | 是 |
| 正向无功电能 | 正向累计无功电能（varh） | 否 |
| 反向无功电能 | 反向累计无功电能（varh） | 否 |
| 视在功率 | 视在功率（VA） | 否 |
| 无功功率 | 无功功率（var） | 否 |
| 电压 | 电压（V） | 否 |
| 电流 | 电流（A） | 否 |
| 功率因数 | 有功功率与视在功率之比，无单位 | 否 |
| 频率 | 电网频率（Hz），仅 ecoMain 提供 | 否 |

具体可用测量取决于设备寄存器，并非所有类别都具有三相总值或每通道值；ecoSub 提供通道测量。云端仅提供**有功功率**和**电能**，默认均启用；电能选项同时控制累计电能与每分钟原始增量。ecoPlug 仍使用固定的开关、功率、电能实体。

### 自定义公式实体

用测量数据创建新传感器，例如计算两路功率的差值或平均值。

1. 在 ecoMain 添加流程或**配置**中选择**添加公式实体**。
2. 填写名称，从下拉菜单选择结果类型，再从来源下拉菜单多选当前条目已启用的测量数据。
3. 按下一页的 `a`、`b` 对应关系填写公式，确认结果单位与所选类型一致。

<!-- Screenshot pending: docs/images/ecomain-formula-setup.png -->

> **截图待补：公式名称、结果类型和来源**
>
> ![截图待补：公式名称、结果类型和来源](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-formula-expression.png -->

> **截图待补：填写公式**
>
> ![截图待补：填写公式](docs/images/0_default.png)

| 公式 | 两路功率的计算结果 |
| --- | --- |
| `max(a-b,0)` | a 减 b，小于 0 时取 0 |
| `(a+b)/2` | a 和 b 的平均功率 |

- 支持 `+`、`-`、`*`、`/`、括号及 `abs`、`min`、`max`、`round`。
- 用**编辑公式实体**修改名称、来源或公式；更换结果类型或单位需新建实体。
- 用**移除额外实体**删除公式。取消某类测量前，先删除使用它的公式。
- 数据缺失或无法计算时，结果显示为不可用。

<!-- Screenshot pending: docs/images/ecomain-formula-edit.png -->

> **截图待补：选择要编辑的公式**
>
> ![截图待补：选择要编辑的公式](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-extra-remove.png -->

> **截图待补：选择要移除的额外实体**
>
> ![截图待补：选择要移除的额外实体](docs/images/0_default.png)

### 通道相位（仅本地）

- 本地 ecoMain 条目可在**配置**中选择下一步操作**通道相位**，再选择 ecoMain 或已配置且在线的 ecoSub。
- 页面显示该设备十个通道的当前相位，每个通道可选 **L1、L2、L3**。
- 保存时先读取当前值，仅写入变更项，再读取确认。
- 写入或校验失败会标记相应字段；已成功的修改不会自动回滚，重试前请核对页面值。
- 该页面会修改设备上的相位配置，云端模式不提供此功能。

现有截图来自较早版本，可能尚未展示测量类型或通道相位页面，产品名称大小写也可能与当前版本不同。

<!-- Screenshot pending: docs/images/ecomain-phase-device.png -->

> **截图待补：选择要设置相位的设备**
>
> ![截图待补：选择要设置相位的设备](docs/images/0_default.png)

<!-- Screenshot pending: docs/images/ecomain-channel-phases.png -->

> **截图待补：设置各通道相位**
>
> ![截图待补：设置各通道相位](docs/images/0_default.png)

## 设备命名规则

集成条目创建后，默认标题格式如下：

- **本地模式：** `ecoMain <序列号> (Local)`
- **云端模式：** `ecoMain <序列号> (Cloud)`

示例：

- `ecoMain 12345678 (Local)`
- `ecoMain 12345678 (Cloud)`

---

## 实体命名规则与含义

本集成会创建一系列传感器实体，实体名称默认与实体的 key 一致，便于使用自动化或模板处理。

### 通用命名模式

- **主机（ecoMain）：** 以 `main_` 开头
- **从机（ecoSub #）：** 以 `sub<从机编号>_` 开头
  例如：`sub1_...`、`sub2_...`、`sub3_...`
- **支路通道编号：** `ch1` ~ `ch10`，共 10 路

---

### 本地模式（Modbus）实体说明

本地模式下包含的测点：

- **主机 L1/L2/L3 三相实时功率**
- **主机三相合计功率（L1+L2+L3）实时值**
- **主机 L1/L2/L3 正/反向累计电能**
- **主机三相合计正/反向累计电能**
- **主机 10 路支路通道（ch1–ch10）：**
    - 实时功率
    - 正向累计电能
    - 反向累计电能
- **从机（ecoSub）仅含支路通道（ch1–ch10）：**
    - 实时功率
    - 正向累计电能
    - 反向累计电能

#### 本地实体后缀含义

- `_rt`：实时值（real-time）
- `fwd_total`：**正向**累计电能（正方向累加）
- `rev_total`：**反向**累计电能（反方向累加）

#### 电流互感器（CT）方向说明

每一个支路通道都通过一个 **电流互感器（CT）** 采样电流。
互感器上一般会有一个 **箭头** 表示电流的正方向：

- 如果实际电流方向与箭头方向一致，则认为是 **正向（forward）**；
- 如果实际电流方向与箭头方向相反，则认为是 **反向（reverse）**。

因此：

- `*_energy_fwd_total`：表示 **正向电流** 产生的累计电能；
- `*_energy_rev_total`：表示 **反向电流** 产生的累计电能。

#### 本地模式示例

主机实时功率：

- `main_l1_power_rt`
- `main_l2_power_rt`
- `main_l3_power_rt`
- `main_all_power_rt`

主机累计电能：

- `main_all_energy_fwd_total`
- `main_all_energy_rev_total`

主机支路示例：

- `main_ch1_power_rt`
- `main_ch1_energy_fwd_total`
- `main_ch1_energy_rev_total`

从机支路示例：

- `sub1_ch1_power_rt`
- `sub1_ch1_energy_fwd_total`
- `sub1_ch1_energy_rev_total`

---

### 云端模式实体说明

云端模式下包含的测点：

- **主机合计（L1+L2+L3）：**
    - 1 分钟平均功率
    - 1 分钟累计电能
- **主机 10 路支路通道（ch1–ch10）：**
    - 1 分钟平均功率
    - 1 分钟累计电能
- **从机（ecoSub）仅含支路通道（ch1–ch10）：**
    - 1 分钟平均功率
    - 1 分钟累计电能

> 云端返回的数据为后端根据配置处理后的结果，非原始瞬时量。

#### 云端实体后缀含义

- `avg_1m`：1 分钟平均值（average in 1 minute）
- `total_1m`：云端接口返回的原始 1 分钟电能增量
- `energy_accumulated`：Home Assistant 侧累加生成的累计电能表

- Home Assistant 能源面板请使用 `*_energy_accumulated` 实体。
- 实时功率监控请使用 `*_power_avg_1m` 实体。
- 原有的云端 `*_energy_total_1m` 实体会继续保留，但它们表示每分钟增量，不是累计电表。

- 云端接口未提供每分钟电能值的时间戳或样本 ID，累计电能可能有误差。
- 出现重复云端数据或 Home Assistant 重启时，结果可能不如记录设备使用以来总电能的本地 Modbus 电表准确。

#### 云端模式示例

主机合计：

- `main_all_power_avg_1m`
- `main_all_energy_total_1m`
- `main_all_energy_accumulated`

主机支路：

- `main_ch1_power_avg_1m`
- `main_ch1_energy_total_1m`
- `main_ch1_energy_accumulated`

从机支路：

- `sub1_ch1_power_avg_1m`
- `sub1_ch1_energy_total_1m`
- `sub1_ch1_energy_accumulated`

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

### Q2：提示 “未找到兼容的设备”（`no_devices_found`）

该错误可能在多处出现：

- 自动发现结束后，没有发现任何 ecoMain 设备。
- 云端登录成功，但账号下没有绑定 ecoMain 主机。
- 在云端选择的主机未返回有效数据。

**排查建议：**

- 对于 **本地模式**：
    - 确认 ecoMain 已上电并接入局域网。
    - 尝试使用 **手动设置（本地）**，直接填写已知 IP。
- 对于 **云端模式**：
    - 登录 enecess App 或 Web 云平台，确认 ecoMain 已经绑定在当前 **enecess App 账号** 下。

---

### Q3：提示 “无法连接到设备”（`cannot_connect_local`）

此错误来自本地 Modbus 客户端在通过固件版本检查后仍无法读取设备。

**常见原因：**

- IP / 主机名填写错误。
- 防火墙阻断了 502 端口。
- ecoMain 与 Home Assistant 不在可达网络中。
- ecoMain 正在重启或异常。

**排查建议：**

1. 检查 ecoMain IP / 主机名是否正确。
2. 在同一网络的其他终端上尝试 ping 此 IP。
3. 确认路由器或防火墙未阻断 **TCP 502 端口**。
4. 尝试重启 ecoMain，再重新添加集成。

---

### Q4：提示 “设备固件版本过低”（`firmware_too_old`）

在本地模式添加过程中，集成首先会读取设备的 **固件版本寄存器**。如果：

- 读取到的固件版本 **低于集成要求的最低版本**，或者
- 无法正确读取固件版本寄存器，

则会提示：**“设备固件版本过低”**（`firmware_too_old`）。

**这代表什么？**

- 当前 ecoMain 固件版本与本集成 **不兼容或过旧**。
- 设备可能运行的是早期固件版本。

**建议处理方式：**

1. 使用官方提供的 enecess 工具 / App / 升级方法，将 ecoMain 更新到 **最新固件版本**。
2. 升级完成后，再次尝试通过本地模式添加集成。
3. 如不清楚如何升级固件，可联系安装服务商或 enecess 官方支持，并说明 Home Assistant 集成提示 `firmware_too_old`。

> 注意：在某些情况下，如果固件寄存器读取失败，本集成也会以 `firmware_too_old` 处理。如果你确认设备固件已是最新，请同时检查网络连通性（IP、端口、接线等）。

---

### Q5：提示 “无法连接到云服务”（`cannot_connect`）

表示集成无法访问 enecess 云端服务。

**可能原因：**

- Home Assistant 无法访问互联网。
- DNS 解析失败。
- 云端接口（例如 `https://hems.enecess.com`）暂时不可用。

**排查建议：**

1. 确认 Home Assistant 主机具有正常外网访问能力。
2. 在同一网络中用浏览器或 `curl` 访问云端地址，看是否可达。
3. 如为云端临时故障，稍后再试。

---

### Q6：提示 “用户名或密码无效”（`auth_failed`）

云端登录时，enecess API 拒绝了你提供的账号密码。

**请注意：** 集成使用的就是你 **enecess App** 的账号密码。如果在 App 中都登录不了，在集成中也同样无法登录。

**排查建议：**

1. 再次确认用户名和密码是否与 enecess App 中使用的一致。
2. 尝试在 enecess 官方 App / Web 云平台，用同样的账号密码登录。
3. 如果在 App 中也无法登录，请先在 App / Web 平台中**修改密码或找回账号**，再回到集成中重新填写。

---

### Q7：提示 “该设备已配置”（`already_configured`）

本集成为每个 ecoMain 及模式组合设置了一个 **唯一 ID**：

- 本地模式：`ecomain:<序列号>:mode_local`
- 云端模式：`ecomain:<序列号>:mode_cloud`

如果已经有相同唯一 ID 的条目存在，就不能再次添加同一个设备 + 模式组合。

**处理方式：**

- 进入 **设置 → 设备与服务**。
- 找到已有的 enecess / ecoMain 条目（序列号相同）。
- 如果需要重新配置，请先删除原条目，再重新添加。

---

### Q8：添加后还能修改哪些配置？

可以从 Home Assistant 的 **配置 / Options** 流程中修改配置：ecoMain 条目可修改已选择的 ecoSub 从机、测量类型、额外实体及本地通道相位，ecoPlug 账号条目可修改已选择的插座。

设备类型、添加方式、已选择的 ecoMain 主设备不可原地修改。如需修改这些不可变配置，请删除现有条目后按新参数重新添加。

---

### Q9：更新集成后，原有条目不工作了

安装新版本前请先查看对应的发布说明。如果更新引入不兼容的配置变更，已有条目可能变为无效状态。

**处理方式：**

1. 删除现有的 enecess 集成条目。
2. 在当前版本下重新添加一次集成。

---

### Q10：为什么只看到部分从机或部分通道？

本集成在创建实体时会使用多层筛选：

1. **配置支持的从机列表**：只支持配置中声明的从机编号（当前为 `1`、`2`、`3`）。
2. **本地模式下的在线从机**：
    - 通过寄存器读取“从机在线状态”。
    - 仅对状态为在线的从机提供选择。
3. **用户选择的从机**：
    - 只为你在流程中勾选的从机创建实体。

最终你能看到的实体是：

- 在支持列表中的从机编号；
- 在本地模式下被检测为在线；
- 并且在配置流程中被你勾选添加的那些。

**如预期中的某个从机或通道没有出现：**

- 检查从机 ecoSub 是否已上电、接线是否正确。
- 删除并重新添加集成，在从机选择步骤中勾选需要的从机。

---

### Q11：为什么有的值总是 0，或者出现负值？

可能原因包括：

- **CT 方向反了：**
    - 如果 CT 箭头安装方向与实际电流方向相反，那么“正向”测点可能始终接近 0，而“反向”测点会不断累加。
    - 请检查互感器安装方向，使箭头与实际电流方向一致。
- **没有负载：**
    - 如果支路上没有接入负载，或当前负载处于关闭状态，则功率和能量的变化都接近于 0。
- **云端与本地模式的差异：**
    - 云端模式返回的是 `avg_1m`（平均值）和 `total_1m`（每分钟累计），数值变化节奏会比本地实时值慢很多。

记住：

- `*_energy_fwd_total`：电流按 **正方向** 流动时产生的累计电能；
- `*_energy_rev_total`：电流按 **反方向** 流动时产生的累计电能。

---

### Q12：云端模式下为什么没有 L1/L2/L3 分相实体？

这是 **设计如此**：

- **本地模式（Modbus）**：
    - 暴露 L1、L2、L3 各相功率 / 电能；
    - 暴露三相合计（L1+L2+L3）数据。
- **云端模式**：
    - 暴露合计（L1+L2+L3）；
    - 暴露各支路通道（ch1–ch10）的数据；
    - 均为处理后的统计值：
        - `*_avg_1m`：一分钟平均功率；
        - `*_total_1m`：一分钟累计电能。

当前云端接口映射中，并未提供按相（L1/L2/L3）的分相数据。

---

### Q13：数据多久更新一次？

- **本地模式**：
    - 集成会以大约 **5 秒** 的间隔轮询 Modbus 寄存器。
    - 带 `_rt` 后缀的实体会近似实时更新。
- **云端模式**：
    - 集成会以大约 **60 秒** 的间隔轮询云端数据。
    - `avg_1m` 和 `total_1m` 是按分钟统计的数据，变化频率相对较慢。

> 实际间隔在后续版本中可能会根据需求进行调整。

---

### Q14：云端账号与密码如何保存，安全吗？

使用 **账号登录（云端）** 时，集成会保存：

- 云端 **用户名**
- 云端 **密码**
- 云端返回的 **token**

它们会保存在 Home Assistant 的配置存储中（和其它集成的敏感信息一样），主要用于：

- 调用云端接口生成 / 刷新 token；
- 查询 ecoMain 主机与从机数据。

**安全建议：**

- 请为 Home Assistant 主机设置强密码，并妥善管理系统备份。
- 如果不再希望通过 Home Assistant 访问 enecess 云端，可以删除 enecess 集成条目。

---

## 支持与反馈

如果你在使用过程中遇到问题，欢迎反馈：

- 尽量附上 Home Assistant 的相关日志。
- 说明你的添加方式（本地自动 / 本地手动 / 云端）。
- 描述你的 ecoMain / ecoSub 型号、安装方式及网络环境。
- 说明看到的具体报错提示（如：`cannot_connect_local`、`firmware_too_old`、`auth_failed` 等）。
