import sys, yaml
from functools import partial
from pimdm.tree import pim_globals
from igmp.igmp2 import igmp_globals
from mld.mld1 import mld_globals
from pimdm import Main


def parse_config_file(file_path):
    """
    Parse yaml file and set everything on protocol process accordingly
    """
    with open(file_path) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        print(data)

        print(type(data.get("UnicastVRF", 254)))

        multicast_vrf = data.get("MulticastVRF", 0)
        pim_globals.MULTICAST_TABLE_ID = multicast_vrf
        pim_globals.UNICAST_TABLE_ID = data.get("UnicastVRF", 254)
        pim_config = data.get("PIM-DM", {})
        igmp_config = data.get("IGMP", {})
        mld_config = data.get("MLD", {})

        ##### PIM config ######
        if "DefaultTimers" in pim_config:
            pim_globals.ASSERT_TIME = pim_config["DefaultTimers"].get("ASSERT_TIME", pim_globals.ASSERT_TIME)
            pim_globals.GRAFT_RETRY_PERIOD = pim_config["DefaultTimers"].get("GRAFT_RETRY_PERIOD", pim_globals.GRAFT_RETRY_PERIOD)
            pim_globals.JP_OVERRIDE_INTERVAL = pim_config["DefaultTimers"].get("JP_OVERRIDE_INTERVAL", pim_globals.JP_OVERRIDE_INTERVAL)
            pim_globals.OVERRIDE_INTERVAL = pim_config["DefaultTimers"].get("OVERRIDE_INTERVAL", pim_globals.OVERRIDE_INTERVAL)
            pim_globals.PROPAGATION_DELAY = pim_config["DefaultTimers"].get("PROPAGATION_DELAY", pim_globals.PROPAGATION_DELAY)
            pim_globals.REFRESH_INTERVAL = pim_config["DefaultTimers"].get("REFRESH_INTERVAL", pim_globals.REFRESH_INTERVAL)
            pim_globals.SOURCE_LIFETIME = pim_config["DefaultTimers"].get("SOURCE_LIFETIME", pim_globals.SOURCE_LIFETIME)
            pim_globals.T_LIMIT = pim_config["DefaultTimers"].get("T_LIMIT", pim_globals.T_LIMIT)

        if "Interfaces" in pim_config:
            interface_dict = pim_config["Interfaces"]
            add_pim_interface_dict = {
                'ipv4': partial(Main.add_pim_interface, ipv4=True, ipv6=False),
                'ipv6': partial(Main.add_pim_interface, ipv4=False, ipv6=True),
            }

            for if_name, ip_family_dict in interface_dict.items():
                for ip_family, if_dict in ip_family_dict.items():
                    if if_dict.get("enabled", False):
                        try:
                            add_pim_interface_dict[ip_family](
                                interface_name=if_name,
                                state_refresh_capable=if_dict.get("state_refresh", False),
                            )
                        except Exception as e:
                            print(e, file=sys.stderr)


        ##### IGMP config #######
        if "Settings" in igmp_config:
            igmp_globals.ROBUSTNESS_VARIABLE = igmp_config["Settings"].get("ROBUSTNESS_VARIABLE", igmp_globals.ROBUSTNESS_VARIABLE)
            igmp_globals.QUERY_INTERVAL = igmp_config["Settings"].get("QUERY_INTERVAL", igmp_globals.QUERY_INTERVAL)
            igmp_globals.QUERY_RESPONSE_INTERVAL = igmp_config["Settings"].get("QUERY_RESPONSE_INTERVAL", igmp_globals.QUERY_RESPONSE_INTERVAL)
            igmp_globals.MAX_RESPONSE_TIME_QUERY_RESPONSE_INTERVAL = igmp_config["Settings"].get("MAX_RESPONSE_TIME_QUERY_RESPONSE_INTERVAL", igmp_globals.QUERY_RESPONSE_INTERVAL*10)
            igmp_globals.GROUP_MEMBERSHIP_INTERVAL = igmp_config["Settings"].get("GROUP_MEMBERSHIP_INTERVAL", igmp_globals.ROBUSTNESS_VARIABLE * igmp_globals.QUERY_INTERVAL + igmp_globals.QUERY_RESPONSE_INTERVAL)
            igmp_globals.OTHER_QUERIER_PRESENT_INTERVAL = igmp_config["Settings"].get("OTHER_QUERIER_PRESENT_INTERVAL", igmp_globals.ROBUSTNESS_VARIABLE * igmp_globals.QUERY_INTERVAL + igmp_globals.QUERY_RESPONSE_INTERVAL / 2)
            igmp_globals.STARTUP_QUERY_INTERVAL = igmp_config["Settings"].get("STARTUP_QUERY_INTERVAL", igmp_globals.QUERY_INTERVAL / 4)
            igmp_globals.STARTUP_QUERY_COUNT = igmp_config["Settings"].get("STARTUP_QUERY_COUNT", igmp_globals.ROBUSTNESS_VARIABLE)
            igmp_globals.LAST_MEMBER_QUERY_INTERVAL = igmp_config["Settings"].get("LAST_MEMBER_QUERY_INTERVAL", igmp_globals.LAST_MEMBER_QUERY_INTERVAL)
            igmp_globals.MAX_RESPONSE_TIME_LAST_MEMBER_QUERY_INTERVAL = igmp_config["Settings"].get("LAST_MEMBER_QUERY_COUNT", igmp_globals.LAST_MEMBER_QUERY_INTERVAL * 10)
            igmp_globals.LAST_MEMBER_QUERY_COUNT = igmp_config["Settings"].get("LAST_MEMBER_QUERY_COUNT", igmp_globals.ROBUSTNESS_VARIABLE)
            igmp_globals.UNSOLICITED_REPORT_INTERVAL = igmp_config["Settings"].get("UNSOLICITED_REPORT_INTERVAL", igmp_globals.UNSOLICITED_REPORT_INTERVAL)
            igmp_globals.VERSION_1_ROUTER_PRESENT_TIMEOUT = igmp_config["Settings"].get("VERSION_1_ROUTER_PRESENT_TIMEOUT", igmp_globals.VERSION_1_ROUTER_PRESENT_TIMEOUT)

        if "Interfaces" in igmp_config:
            interface_dict = igmp_config["Interfaces"]

            for if_name, if_value in interface_dict.items():
                try:
                    if if_value.get("enabled", False):
                        Main.add_membership_interface(interface_name=if_name, ipv4=True, ipv6=False)
                except Exception as e:
                    print(e, file=sys.stderr)

        ##### MLD config #######
        if "Settings" in mld_config:
            mld_globals.ROBUSTNESS_VARIABLE = mld_config["Settings"].get("ROBUSTNESS_VARIABLE", mld_globals.ROBUSTNESS_VARIABLE)
            mld_globals.QUERY_INTERVAL = mld_config["Settings"].get("QUERY_INTERVAL", mld_globals.QUERY_INTERVAL)
            mld_globals.QUERY_RESPONSE_INTERVAL = mld_config["Settings"].get("QUERY_RESPONSE_INTERVAL", mld_globals.QUERY_RESPONSE_INTERVAL)
            mld_globals.MULTICAST_LISTENER_INTERVAL = mld_config["Settings"].get("MULTICAST_LISTENER_INTERVAL", (mld_globals.ROBUSTNESS_VARIABLE * mld_globals.QUERY_INTERVAL) + (mld_globals.QUERY_RESPONSE_INTERVAL))
            mld_globals.OTHER_QUERIER_PRESENT_INTERVAL = mld_config["Settings"].get("OTHER_QUERIER_PRESENT_INTERVAL", (mld_globals.ROBUSTNESS_VARIABLE * mld_globals.QUERY_INTERVAL) + 0.5 * mld_globals.QUERY_RESPONSE_INTERVAL)
            mld_globals.STARTUP_QUERY_INTERVAL = mld_config["Settings"].get("STARTUP_QUERY_INTERVAL", (1 / 4) * mld_globals.QUERY_INTERVAL)
            mld_globals.STARTUP_QUERY_COUNT = mld_config["Settings"].get("STARTUP_QUERY_COUNT", mld_globals.ROBUSTNESS_VARIABLE)
            mld_globals.LAST_LISTENER_QUERY_INTERVAL = mld_config["Settings"].get("LAST_LISTENER_QUERY_INTERVAL", mld_globals.LAST_LISTENER_QUERY_INTERVAL)
            mld_globals.LAST_LISTENER_QUERY_COUNT = mld_config["Settings"].get("LAST_LISTENER_QUERY_COUNT", mld_globals.ROBUSTNESS_VARIABLE)
            mld_globals.UNSOLICITED_REPORT_INTERVAL = mld_config["Settings"].get("UNSOLICITED_REPORT_INTERVAL", mld_globals.UNSOLICITED_REPORT_INTERVAL)

        if "Interfaces" in mld_config:
            interface_dict = mld_config["Interfaces"]

            for if_name, if_value in interface_dict.items():
                try:
                    if if_value.get("enabled", False):
                        Main.add_membership_interface(interface_name=if_name, ipv4=False, ipv6=True)
                except Exception as e:
                    print(e, file=sys.stderr)


def get_yaml_file():
    """
    Get configuration file from live protocol process
    """
    dict_file = {
        'MulticastVRF': pim_globals.MULTICAST_TABLE_ID,
        'UnicastVRF': pim_globals.UNICAST_TABLE_ID,
        'PIM-DM': {
            "DefaultTimers": {
                "ASSERT_TIME": pim_globals.ASSERT_TIME,
                "GRAFT_RETRY_PERIOD": pim_globals.GRAFT_RETRY_PERIOD,
                "JP_OVERRIDE_INTERVAL": pim_globals.JP_OVERRIDE_INTERVAL,
                "OVERRIDE_INTERVAL": pim_globals.OVERRIDE_INTERVAL,
                "PROPAGATION_DELAY": pim_globals.PROPAGATION_DELAY,
                "REFRESH_INTERVAL": pim_globals.REFRESH_INTERVAL,
                "SOURCE_LIFETIME": pim_globals.SOURCE_LIFETIME,
                "T_LIMIT": pim_globals.T_LIMIT,
            },
            "Interfaces": {},
        },
        'IGMP': {
            "Settings": {
                "ROBUSTNESS_VARIABLE": igmp_globals.ROBUSTNESS_VARIABLE,
                "QUERY_INTERVAL": igmp_globals.QUERY_INTERVAL,
                "QUERY_RESPONSE_INTERVAL": igmp_globals.QUERY_RESPONSE_INTERVAL,
                "MAX_RESPONSE_TIME_QUERY_RESPONSE_INTERVAL": igmp_globals.MAX_RESPONSE_TIME_QUERY_RESPONSE_INTERVAL,
                "GROUP_MEMBERSHIP_INTERVAL": igmp_globals.GROUP_MEMBERSHIP_INTERVAL,
                "OTHER_QUERIER_PRESENT_INTERVAL": igmp_globals.OTHER_QUERIER_PRESENT_INTERVAL,
                "STARTUP_QUERY_INTERVAL": igmp_globals.STARTUP_QUERY_INTERVAL,
                "STARTUP_QUERY_COUNT": igmp_globals.STARTUP_QUERY_COUNT,
                "LAST_MEMBER_QUERY_INTERVAL": igmp_globals.LAST_MEMBER_QUERY_INTERVAL,
                "MAX_RESPONSE_TIME_LAST_MEMBER_QUERY_INTERVAL": igmp_globals.MAX_RESPONSE_TIME_LAST_MEMBER_QUERY_INTERVAL,
                "LAST_MEMBER_QUERY_COUNT": igmp_globals.LAST_MEMBER_QUERY_COUNT,
                "UNSOLICITED_REPORT_INTERVAL": igmp_globals.UNSOLICITED_REPORT_INTERVAL,
                "VERSION_1_ROUTER_PRESENT_TIMEOUT": igmp_globals.VERSION_1_ROUTER_PRESENT_TIMEOUT,
            },
            "Interfaces": {},
        },
        'MLD': {
            "Settings": {
                "ROBUSTNESS_VARIABLE": mld_globals.ROBUSTNESS_VARIABLE,
                "QUERY_INTERVAL": mld_globals.QUERY_INTERVAL,
                "QUERY_RESPONSE_INTERVAL": mld_globals.QUERY_RESPONSE_INTERVAL,
                "MULTICAST_LISTENER_INTERVAL": mld_globals.MULTICAST_LISTENER_INTERVAL,
                "OTHER_QUERIER_PRESENT_INTERVAL": mld_globals.OTHER_QUERIER_PRESENT_INTERVAL,
                "STARTUP_QUERY_INTERVAL": mld_globals.STARTUP_QUERY_INTERVAL,
                "STARTUP_QUERY_COUNT": mld_globals.STARTUP_QUERY_COUNT,
                "LAST_LISTENER_QUERY_INTERVAL": mld_globals.LAST_LISTENER_QUERY_INTERVAL,
                "LAST_LISTENER_QUERY_COUNT": mld_globals.LAST_LISTENER_QUERY_COUNT,
                "UNSOLICITED_REPORT_INTERVAL": mld_globals.UNSOLICITED_REPORT_INTERVAL,
            },
            "Interfaces": {},
        }
    }

    for if_name, if_value in Main.interfaces.items():
        dict_file["PIM-DM"]["Interfaces"][if_name] = {}
        dict_file["PIM-DM"]["Interfaces"][if_name]["ipv4"] = {
            "enabled": True,
        }

    for if_name, if_value in Main.interfaces_v6.items():
        if if_name not in dict_file["PIM-DM"]["Interfaces"]:
            dict_file["PIM-DM"]["Interfaces"][if_name] = {}

        dict_file["PIM-DM"]["Interfaces"][if_name]["ipv6"] = {
            "enabled": True,
        }

    for if_name in Main.igmp_interfaces.keys():
        dict_file["IGMP"]["Interfaces"][if_name] = {
            "enabled": True,
        }

    for if_name in Main.mld_interfaces.keys():
        dict_file["MLD"]["Interfaces"][if_name] = {
            "enabled": True,
        }

    return yaml.dump(dict_file)


def get_vrfs(file_path):
    """
    Get vrf configuration from yaml file.
    This is only used by Run.py to create the correct daemons accordingly (daemons are bound to specific VRFs).
    """
    with open(file_path) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        multicast_vrf = data.get("MulticastVRF", 0)
        unicast_vrf = data.get("UnicastVRF", 254)
        return [multicast_vrf, unicast_vrf]
