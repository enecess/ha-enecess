# enecess Home Assistant 集成发布说明

## v1.0.0

发布日期：2026-08-11

v1.0.0 是 enecess Home Assistant 集成的首个稳定版本。本版本延续 v0.1.3 的 EcoMain 与 EcoPlug 功能，并为加入 HACS 默认集成列表完成仓库准备。

### 亮点

- 集成由测试状态转为首个稳定版本。
- 新增 HACS 仓库校验与 Home Assistant Hassfest 工作流。
- 为仓库添加 MIT License。
- 更新英文、德文、法文、波兰文和简体中文文档，以说明标准 HACS 安装方式。
- 继续使用 Home Assistant Brands 仓库中已有的 enecess 品牌素材。

### 兼容性

- EcoMain 继续支持本地 Modbus TCP 与 Enecess Cloud 两种方式。
- EcoPlug 继续通过 Enecess Cloud 使用。
- 已有 v0.1.3 EcoMain 与 EcoPlug 条目无需迁移配置。

### 升级说明

- 通过 HACS 升级，然后重启 Home Assistant。
- 升级前请查看发布说明，并保留最新的 Home Assistant 备份。

---

## v0.1.3

发布日期：2026-07-29

v0.1.3 新增仅云端的 EcoPlug 支持，包括同一账号多选设备、插座开关控制、实时功率与累计电能监测，以及添加后调整所选插座。

### 亮点

- 新增通过 Enecess Cloud 使用的 **EcoPlug** 设备类型。
- 同一个云端账号条目可按名称和序列号选择并管理一个或多个 EcoPlug。
- 每个已选择的 EcoPlug 会创建：
  - 一个通过云端控制开关的实体。
  - 一个以瓦为单位的实时功率传感器。
  - 一个以千瓦时为单位的累计电能传感器。
- 新增 EcoPlug 的 **配置 / Options 流程**，可修改已有账号条目中选择的插座。
- 更新英文、德文、法文、波兰文和简体中文的 EcoPlug 设置界面文案与文档。

### 变更

- 新增 EcoPlug 云端 API 支持，用于读取测量数据、读取开关状态以及发送开关控制命令。
- 新增专用 EcoPlug 云端 coordinator，大约每 60 秒轮询一次。
- 每个插座的数据请求与状态请求独立处理；普通请求失败只影响对应读数或状态，不会丢弃账号下其他可用数据。
- 云端认证过期时会刷新令牌并重试失败操作一次，刷新后的令牌会保存回配置条目。
- 开关命令成功后会立即发布云端已接受的目标状态，后续云端轮询仍作为权威状态来源。
- EcoPlug 添加流程会验证云端凭据、列出兼容硬件、要求至少选择一个插座，并阻止同一云端账号被重复添加。
- EcoPlug Options 会刷新账号当前的插座列表，并在选择发生变化后重新加载条目。
- 新增共享注册表清理逻辑，安全移除已取消选择的 EcoPlug 设备及实体；已有 EcoMain 清理也改用同一辅助模块。
- 集成现在同时转发 sensor 和 switch 平台，同时保持已有 EcoMain 传感器行为不变。

### 升级说明

- 通过 HACS 升级，然后重启 Home Assistant。
- 已有 EcoMain 条目继续使用当前的本地或云端配置及实体。
- 如需添加 EcoPlug，请在添加 enecess 集成时选择 **EcoPlug**，使用 enecess App 账号登录，并选择一个或多个插座。
- 后续如需修改所选插座，请打开 **设置 -> 设备与服务 -> enecess -> 配置**。

### 已知限制

- EcoPlug 仅支持通过 Enecess Cloud 使用，不支持本地添加。
- EcoPlug 条目不支持额外实体（Extra Entities）。
- EcoPlug 数值与状态依赖云端可用性，通常大约每 60 秒刷新一次。

---

## v0.1.2

发布日期：2026-07-27

v0.1.2 改进本地添加 EcoMain 时的连接清理，并限制设备未提供兼容固件版本寄存器时的等待时间。

### 变更

- 固件校验正常完成或提前退出时，本地添加流程现在都会关闭临时 Modbus 客户端。
- 固件寄存器校验现在最多等待 5 秒。v0.1.1 已会在 pymodbus 完成重试后返回 **设备固件版本过低**；v0.1.2 对该等待时间设置了上限。
- 在集成显示固件错误之前，pymodbus 仍可能记录首次收到的不支持或格式异常的 Modbus 响应。
- 固件版本过低或固件寄存器无法读取时，校验会在读取 EcoSub 在线状态寄存器之前停止。
- 固件寄存器地址仍为 3009，最低支持固件版本仍为 136，正常 coordinator 轮询逻辑保持不变。

---

## v0.1.1

发布日期：2026-06-17

v0.1.1 重点改进 EcoMain 首次添加后的可用性，新增可配置的派生传感器实体，并让云端能量数据更适合在 Home Assistant 中使用。

### 亮点

- 新增 EcoMain **Extra Entities**。
  - 可基于已有功率传感器创建反向功率实体。
  - 可基于已有功率传感器创建绝对值功率实体。
  - 可基于多个同类型功率或能量传感器创建求和实体。
  - 可基于多个同类型功率或能量传感器创建平均值实体。
- 新增已有 EcoMain 条目的 **Options / Configure flow**。
  - 添加完成后仍可调整已选择的 EcoSub 从设备。
  - 添加完成后仍可新增或移除 Extra Entities。
  - 选项变更后会自动重新加载集成条目以应用配置。
- 新增云端累计能量传感器。
  - 云端原始 `*_energy_total_1m` 实体现在明确说明为 1 分钟能量增量。
  - 新增 `*_energy_accumulated` 实体，作为 Home Assistant 侧累计能量表，可用于 Energy Dashboard。
- 改进 Home Assistant 传感器元数据。
  - 功率传感器现在带有正确的功率 device class 和 measurement state class。
  - 累计能量传感器现在带有正确的能量 device class 和 total-increasing state class。
  - 数值传感器现在设置了默认建议显示精度。
- 更新设置/选项界面文案，并新增波兰语文档和 Home Assistant 界面翻译。
- 更新 README 文档和截图，补充新的 Extra Entities 与 Options 流程。

### 变更

- 新增共享 EcoMain 选项和实体逻辑的辅助模块：
  - 根据条目数据和可变选项构建实体描述。
  - 为普通传感器和额外传感器生成稳定的 unique ID。
  - 标准化 Extra Entity 配置。
  - 跟踪预期的设备注册表和实体注册表标识。
- 已有条目现在会清理不再被选择的 EcoSub 设备和传感器注册表项。
- 本地和云端 coordinator 现在会基于 entry options 构建 EcoMain specs，因此修改 EcoSub 选择后会在重新加载后生效。
- 云端硬件通道解析更稳健，可处理通道号缺失或非数字的情况。
- 本地发现重复设备时，现在会为已配置的 local-auto 条目更新已保存的 mDNS/IP 数据，而不是启动重复的添加流程。
- 云端主设备选择值已规范为字符串，以提高 selector 兼容性。

### 升级说明

- 通过 HACS 从 v0.1.0 升级，然后重启 Home Assistant。
- 已有条目应可继续工作，但当前集成仍为测试版本。如果升级后条目表现异常，请删除该条目并重新添加。
- 如需编辑已有条目，请打开 **Settings -> Devices & services -> enecess -> Configure**。
- 可变设置：
  - 已选择的 EcoSub 从设备
  - Extra Entity 配置
- 不可变设置：
  - 设备类型
  - 添加方式
  - 已选择的 EcoMain 主设备 / 序列号
- 云端模式下，建议在 Home Assistant Energy Dashboard 中使用 `*_energy_accumulated` 实体。原始 `*_energy_total_1m` 实体是每分钟增量，不是生命周期累计计数器。
- 云端累计能量是尽力计算结果，因为当前云端 API 不提供每个能量增量对应的时间戳或采样 ID。

### 已知限制

- 当前集成仍为测试版本，迁移行为尚未完全定型。
- 修改设备类型、添加方式或已选择的 EcoMain 主设备仍需要删除并重新添加集成条目。
- 云端累计能量的精度可能低于本地 Modbus 生命周期计数器，尤其是在重启或云端样本重复的情况下。

---

## v0.1.0

发布日期：2025-12-30

v0.1.0 是 enecess Home Assistant 自定义集成的第一个测试版本，提供 EcoMain 的初始支持，包括本地 Modbus TCP 和 enecess 云端两种方式。

### 亮点

- 新增 EcoMain 作为 Home Assistant 自定义集成。
- 新增通过 Modbus TCP 连接本地 EcoMain 的支持。
- 新增本地 EcoMain 设备的 zeroconf / mDNS 自动发现。
- 新增通过 EcoMain 序列号和 IP/hostname 的本地手动设置。
- 新增通过 enecess App 账号登录的云端设置。
- 新增设置过程中的 EcoSub 从设备选择。
- 新增 EcoMain 和 EcoSub 的功率、能量传感器实体。
- 新增 HACS custom repository 安装文档。
- 新增多语言 README 文档：
  - 英文
  - 德文
  - 法文
  - 简体中文

### 支持的添加方式

- **Automatic Discovery (Local)**
  - 使用 zeroconf / mDNS 在同一局域网中发现 EcoMain 设备。
  - 用户可选择发现到的 EcoMain，确认设备信息，并选择在线 EcoSub 从设备。
- **Manual Setup (Local)**
  - 用户可手动输入 EcoMain 序列号和 IP/hostname。
  - 通过 Modbus TCP 连接，并检测在线 EcoSub 从设备。
- **Account Login (Cloud)**
  - 使用与官方 enecess App 相同的账号和密码。
  - 从云端账号列出可用的 EcoMain 主设备。
  - 用户可选择可用的 EcoSub 从设备。

### 实体覆盖范围

- 本地模式：
  - EcoMain L1/L2/L3 实时功率。
  - EcoMain 总实时功率。
  - EcoMain 正向 / 反向累计电能。
  - EcoMain 分支通道实时功率和正向 / 反向累计电能。
  - EcoSub 分支通道实时功率和正向 / 反向累计电能。
- 云端模式：
  - EcoMain 总 1 分钟平均功率和 1 分钟电能增量。
  - EcoMain 分支通道 1 分钟平均功率和 1 分钟电能增量。
  - EcoSub 分支通道 1 分钟平均功率和 1 分钟电能增量。

### 已知限制

- v0.1.0 是测试版本。
- v0.1.0 中已有条目不能原地编辑。
- 修改 host、添加方式、已选择从设备或已选择 EcoMain 时，需要删除并重新添加集成条目。
- 升级和迁移行为尚未定型。
- EcoMain 最低支持固件版本未来可能变化。
