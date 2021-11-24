# PIM-DM

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pim-dm)](https://pypi.org/project/pim-dm/)
[![PyPI](https://img.shields.io/pypi/v/pim-dm)](https://pypi.org/project/pim-dm/)
[![PyPI - License](https://img.shields.io/pypi/l/pim-dm)](https://github.com/pedrofran12/pim_dm/blob/master/LICENSE)

We have implemented PIM-DM specification ([RFC3973](https://tools.ietf.org/html/rfc3973)).

This repository stores the implementation of this protocol. The implementation is written in Python language and is destined to Linux systems.

Additionally, IGMPv2 and MLDv1 are implemented alongside with PIM-DM to detect interest of hosts.


# Requirements

 - Linux machine
 - Unicast routing protocol
 - Python3 (we have written all code to be compatible with at least Python v3.3)
 - pip (to install all dependencies)
 - tcpdump


# Installation

  ```
  pip3 install pim-dm 
  ```



# Run PIM-DM protocol

You may need sudo permissions, in order to run this protocol. This is required because we use raw sockets to exchange control messages. For this reason, some sockets to work properly need to have super user permissions.

To interact with the protocol you need to execute the `pim-dm` command. You may need to specify a command and corresponding arguments:

   `pim-dm -COMMAND ARGUMENTS`


#### Start protocol process

In order to start the protocol you first need to explicitly start it. This will start a daemon process, which will be running in the background. The command is the following:
  ```
  sudo pim-dm -start [-mvrf MULTICAST_TABLE_ID] [-uvrf UNICAST_TABLE_ID]
  ```

IPv4 and IPv6 multicast is supported. By default all commands will be executed on IPv4 daemon. To execute a command on the IPv6 daemon use `-6`. 

We support multiple tables. Each daemon process will be bind to a given multicast and unicast table id, which can be defined at startup with `-mvrf` and `-uvrf`.

If `-mvrf` is not defined, the default multicast table id will be used (table id 0).

If `-uvrf` is not defined, the default unicast table id will be used (table id 254).

After starting the protocol process, if the default multicast table is not used, the following commands (for adding interfaces and listing state) need to have the argument `-mvrf` defined to specify the corresponding daemon process.



#### Multi daemon support

Multiple daemons are supported, each bind to a given multicast routing table id.

To perform configurations on one of these daemons use `-mvrf` command and define the daemon by its multicast table id.


To see all daemons that are currently running:

   ```
   sudo pim-dm -instances
   ```

#### Add interface

After starting the protocol process you can enable the protocol in specific interfaces. You need to specify which interfaces will have IGMP enabled and which interfaces will have PIM-DM enabled.

- To enable PIM-DM without State-Refresh, in a given interface, you need to run the following command:

   ```
   sudo pim-dm -ai INTERFACE_NAME [-4 | -6] [-mvrf MULTICAST_TABLE_ID]
   ```

- To enable PIM-DM with State-Refresh, in a given interface, you need to run the following command:

   ```
   sudo pim-dm -aisr INTERFACE_NAME [-4 | -6] [-mvrf MULTICAST_TABLE_ID]
   ```

- To enable IGMP/MLD in a given interface, you need to run the following command:

   - IGMP:
   ```
   sudo pim-dm -aiigmp INTERFACE_NAME [-mvrf MULTICAST_TABLE_ID]
   ```

   - MLD:
   ```
   sudo pim-dm -aimld INTERFACE_NAME [-mvrf MULTICAST_TABLE_ID]
   ```

#### Remove interface

To remove a previously added interface, you need run the following commands:

- To remove a previously added PIM-DM interface:

   ```
   sudo pim-dm -ri INTERFACE_NAME [-4 | -6] [-mvrf MULTICAST_TABLE_ID]
   ```

- To remove a previously added IGMP/MLD interface:
   - IGMP:
   ```
   sudo pim-dm -riigmp INTERFACE_NAME [-mvrf MULTICAST_TABLE_ID]
   ```

   - MLD:
   ```
   sudo pim-dm -rimld INTERFACE_NAME [-mvrf MULTICAST_TABLE_ID]
   ```


#### Stop protocol process

If you want to stop the protocol process, and stop the daemon process, you need to explicitly run this command:

If a specific multicast table id was defined on startup, you need to define the daemon by its multicast table id.

   ```
   sudo pim-dm -stop [-mvrf MULTICAST_TABLE_ID]
   ```



## Commands for monitoring the protocol process
We have built some list commands that can be used to check the "internals" of the implementation.

 - #### List interfaces:

	 Show all router interfaces and which ones have PIM-DM and IGMP/MLD enabled. For IGMP/MLD enabled interfaces you can check the Querier state.

   ```
   sudo pim-dm -li [-4 | -6] [-mvrf MULTICAST_TABLE_ID]
   ```

 - #### List neighbors
	 Verify neighbors that have established a neighborhood relationship.

   ```
   sudo pim-dm -ln [-4 | -6] [-mvrf MULTICAST_TABLE_ID]
   ```

 - #### List state
    List all state machines and corresponding state of all trees that are being monitored. Also list IGMP state for each group being monitored.

   ```
   sudo pim-dm -ls [-4 | -6] [-mvrf MULTICAST_TABLE_ID]
   ```

 - #### Multicast Routing Table
   List Linux Multicast Routing Table (equivalent to `ip mroute show`)

   ```
   sudo pim-dm -mr [-4 | -6] [-mvrf MULTICAST_TABLE_ID]
   ```

## Config File

It is possible to configure the protocol using a YAML file. This configuration file can be used to set all interfaces that will have PIM-DM/IGMP/MLD enabled, as well to fine tune these protocols by setting their timers. Currently the settings are shared by all interfaces. In a future release it will be possible to set timers per interface.

To use this feature you need to manually install PyYaml. PyYaml is not automatically installed with `pim-dm` to support older Python versions (as of now PyYaml requires at least Python v3.5).

[This YAML file](https://github.com/pedrofran12/pim_dm/tree/master/config/config_example.yml) is a configuration file example.

It it also possible to get an YAML configuration file from the current settings of the daemon. This will output an YAML template that can be used later for enabling the daemon with the same settings (enabled interfaces and timers). The command for this matter is the following:

   ```
   sudo pim-dm -get_config [-mvrf MULTICAST_TABLE_ID]
   ```

To input an YAML configuration file to the daemon:

   ```
   sudo pim-dm -config CONFIGURATION_FILE_PATH
   ```


## Help command
In order to determine which commands and corresponding arguments are available you can call the help command:

   ```
   pim-dm -h
   ```


## Tests

We have performed tests to our PIM-DM implementation. You can check on the corresponding branches:

- [Test_PIM_Hello](https://github.com/pedrofran12/pim_dm/tree/Test_PIM_Hello) - Topology used to test the establishment of adjacency between routers.
- [Test_PIM_BroadcastTree](https://github.com/pedrofran12/pim_dm/tree/Test_PIM_BroadcastTree) - Topology used to test our implementation regarding the creation and maintenance of the broadcast tree.
- [Test_PIM_Assert](https://github.com/pedrofran12/pim_dm/tree/Test_PIM_Assert) - Topology used to test the election of the AssertWinner.
- [Test_PIM_Join_Prune_Graft](https://github.com/pedrofran12/pim_dm/tree/Test_PIM_Join_Prune_Graft) - Topology used to test the Pruning and Grafting of the multicast distribution tree.
- [Test_PIM_StateRefresh](https://github.com/pedrofran12/pim_dm/tree/Test_PIM_StateRefresh) - Topology used to test PIM-DM State Refresh.
- [Test_IGMP](https://github.com/pedrofran12/pim_dm/tree/Test_IGMP) - Topology used to test our IGMPv2 implementation.
