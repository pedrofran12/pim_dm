# PIM-DM

We have implemented PIM-DM specification ([RFC3973](https://tools.ietf.org/html/rfc3973)).

This repository stores the implementation of this protocol. The implementation is written in Python language and is destined to Linux systems.


# Requirements

 - Linux machine
 - Python3 (we have written all code to be compatible with at least Python v3.2)
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
  sudo pim-dm -start
  ```


#### Add interface

After starting the protocol process you can enable the protocol in specific interfaces. You need to specify which interfaces will have IGMP enabled and which interfaces will have PIM-DM enabled.

- To enable PIM-DM without State-Refresh, in a given interface, you need to run the following command:

   ```
   sudo pim-dm -ai INTERFACE_NAME
   ```

- To enable PIM-DM with State-Refresh, in a given interface, you need to run the following command:

   ```
   sudo pim-dm -aisf INTERFACE_NAME
   ```

- To enable IGMP in a given interface, you need to run the following command:

   ```
   sudo pim-dm -aiigmp INTERFACE_NAME
   ```

#### Remove interface

To remove a previously added interface, you need run the following commands:

- To remove a previously added PIM-DM interface:

   ```
   sudo pim-dm -ri INTERFACE_NAME
   ```

- To remove a previously added IGMP interface:

   ```
   sudo pim-dm -riigmp INTERFACE_NAME
   ```


#### Stop protocol process

If you want to stop the protocol process, and stop the daemon process, you need to explicitly run this command:

   ```
   sudo pim-dm -stop
   ```



## Commands for monitoring the protocol process
We have built some list commands that can be used to check the "internals" of the implementation.

 - #### List interfaces:

	 Show all router interfaces and which ones have PIM-DM and IGMP enabled. For IGMP enabled interfaces check the IGMP Querier state.

   ```
   sudo pim-dm -li
   ```

 - #### List neighbors
	 Verify neighbors that have established a neighborhood relationship.

   ```
   sudo pim-dm -ln
   ```

 - #### List state
    List all state machines and corresponding state of all trees that are being monitored. Also list IGMP state for each group being monitored.

   ```
   sudo pim-dm -ls
   ```

 - #### Multicast Routing Table
   List Linux Multicast Routing Table (equivalent to `ip mroute -show`)

   ```
   sudo pim-dm -mr
   ```


## Help command
In order to determine which commands and corresponding arguments are available you can call the help command:

   ```
   pim-dm -h
   ```

   or

   ```
   pim-dm --help
   ```

## Change settings

Files tree/globals.py and igmp/igmp_globals.py store all timer values and some configurations regarding IGMP and the PIM-DM. If you want to tune the implementation, you can change the values of these files. These configurations are used by all interfaces, meaning that there is no tuning per interface.


## Tests

We have performed tests to our PIM-DM implementation. You can check on the corresponding branches:

- [Test_PIM_Hello](https://github.com/pedrofran12/pim_dm/tree/Test_PIM_Hello) - Topology used to test the establishment of adjacency between routers.
- [Test_PIM_BroadcastTree](https://github.com/pedrofran12/pim_dm/tree/Test_PIM_BroadcastTree) - Topology used to test our implementation regarding the creation and maintenance of the broadcast tree.
- [Test_PIM_Assert](https://github.com/pedrofran12/pim_dm/tree/Test_PIM_Assert) - Topology used to test the election of the AssertWinner.
- [Test_PIM_Join_Prune_Graft](https://github.com/pedrofran12/pim_dm/tree/Test_PIM_Join_Prune_Graft) - Topology used to test the Pruning and Grafting of the multicast distribution tree.
- [Test_PIM_StateRefresh](https://github.com/pedrofran12/pim_dm/tree/Test_PIM_StateRefresh) - Topology used to test PIM-DM State Refresh.
- [Test_IGMP](https://github.com/pedrofran12/hpim_dm/tree/Test_IGMP) - Topology used to test our IGMPv2 implementation.
