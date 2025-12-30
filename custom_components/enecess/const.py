from dataclasses import dataclass
from typing import Optional

DOMAIN = "enecess"

# entry config
CONST_ENTRY_ENECESS_API = "enecess_api"
CONST_ENTRY_MODBUS_CLIENT = "modbus_client"
CONST_ENTRY_COORDINATOR = "coordinator"

CONST_DEVICE_TYPE = "device_type"

# device types
CONST_DEVICE_ECOMAIN = "ecomain"

# local config
CONST_MDNS_NAME = "mdns_name"
CONST_MDNS_IP = "mdns_ip"

# cloud config
CONST_CLOUD_HEADER_TOKEN = "Access-Token"
CONST_CLOUD_USERNAME = "username"
CONST_CLOUD_PASSWORD = "password"
CONST_CLOUD_TOKEN = "token"

CONF_CLOUD_BASE_URL = "https://hems.enecess.com"

# add mode
CONST_ADD_MODE = "mode"
CONST_ADD_MODE_LOCAL = "local"
CONST_ADD_MODE_LOCAL_AUTO = "auto"
CONST_ADD_MODE_LOCAL_MANUAL = "manual"
CONST_ADD_MODE_CLOUD = "cloud"

# EcoMain config
CONST_ECOMAIN_HOST = "ecomain_host"
CONST_ECOMAIN_PORT = "ecomain_port"
CONF_ECOMAIN_PORT = 502

CONST_ECOMAIN_SERIAL = "ecomain_serial"
CONST_ECOMAIN_MASTERS = "ecomain_masters"
CONST_ECOMAIN_SELECTED_SLAVES = "ecomain_selected_slaves"
CONST_ECOMAIN_ONLINE_SLAVES = "ecomain_online_slaves"

CONF_ECOMAIN_AVAILABLE_SLAVES = ["1", "2", "3"]
CONF_ECOMAIN_MDNS_PREFIX = "enecess-main-"
CONF_ECOMAIN_MDNS_TYPE = "_http._tcp.local."
CONF_ECOMAIN_UNIT_ID = 255
CONF_ECOMAIN_MIN_FIRMWARE_VERSION = 136
CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER = 3009
CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_START = 3101
CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_COUNT = 3

CONST_ECOMAIN_CLOUD_MASTER_ID = "ecomain_cloud_master_id"
CONST_ECOMAIN_CLOUD_MASTER = "ecomain_cloud_master"
CONST_ECOMAIN_CLOUD_SLAVES = "ecomain_cloud_slaves"
CONST_ECOMAIN_CLOUD_SLAVE_MAP = "ecomain_cloud_slave_map"

# time intervals
CONF_LOCAL_MDNS_SCAN_INTERVAL = 3
CONF_LOCAL_UPDATE_INTERVAL = 5
CONF_CLOUD_UPDATE_INTERVAL = 60


@dataclass(frozen=True)
class DiscoveryConfig:
    mdns_type: str
    mdns_prefix: str


@dataclass(frozen=True)
class DeviceType:
    discovery: Optional[DiscoveryConfig]


@dataclass(frozen=True)
class EcoMainDeviceTyp(DeviceType):
    available_slaves: Optional[list[str]]


DEVICE_CONFIGS: dict[str, DeviceType] = {
    CONST_DEVICE_ECOMAIN: EcoMainDeviceTyp(
        available_slaves=CONF_ECOMAIN_AVAILABLE_SLAVES,
        discovery=DiscoveryConfig(
            mdns_type=CONF_ECOMAIN_MDNS_TYPE,
            mdns_prefix=CONF_ECOMAIN_MDNS_PREFIX,
        ),
    ),
}
