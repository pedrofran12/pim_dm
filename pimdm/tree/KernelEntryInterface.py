from pimdm import Main
from abc import abstractmethod, ABCMeta


class KernelEntryInterface(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def get_outbound_interfaces_indexes(kernel_tree):
        """
        Get OIL of this tree
        """
        pass

    @staticmethod
    @abstractmethod
    def get_interface_name(interface_id):
        """
        Get name of interface from vif id
        """
        pass

    @staticmethod
    @abstractmethod
    def get_interface(kernel_tree, interface_id):
        """
        Get PIM interface from interface id
        """
        pass

    @staticmethod
    @abstractmethod
    def get_membership_interface(kernel_tree, interface_id):
        """
        Get IGMP/MLD interface from interface id
        """
        pass

    @staticmethod
    @abstractmethod
    def get_kernel():
        """
        Get kernel
        """
        pass


class KernelEntry4Interface(KernelEntryInterface):
    @staticmethod
    def get_outbound_interfaces_indexes(kernel_tree):
        """
        Get OIL of this tree
        """
        outbound_indexes = [0] * Main.kernel.MAXVIFS
        for (index, state) in kernel_tree.interface_state.items():
            outbound_indexes[index] = state.is_forwarding()
        return outbound_indexes

    @staticmethod
    def get_interface_name(interface_id):
        """
        Get name of interface from vif id
        """
        return Main.kernel.vif_index_to_name_dic[interface_id]

    @staticmethod
    def get_interface(kernel_tree, interface_id):
        """
        Get PIM interface from interface id
        """
        interface_name = kernel_tree.get_interface_name(interface_id)
        return Main.interfaces.get(interface_name, None)

    @staticmethod
    def get_membership_interface(kernel_tree, interface_id):
        """
        Get IGMP interface from interface id
        """
        interface_name = kernel_tree.get_interface_name(interface_id)
        return Main.igmp_interfaces.get(interface_name, None)  # type: InterfaceIGMP

    @staticmethod
    def get_kernel():
        """
        Get kernel
        """
        return Main.kernel


class KernelEntry6Interface(KernelEntryInterface):
    @staticmethod
    def get_outbound_interfaces_indexes(kernel_tree):
        """
        Get OIL of this tree
        """
        outbound_indexes = [0] * 8
        for (index, state) in kernel_tree.interface_state.items():
            outbound_indexes[index // 32] |= state.is_forwarding() << (index % 32)
        return outbound_indexes

    @staticmethod
    def get_interface_name(interface_id):
        """
        Get name of interface from vif id
        """
        return Main.kernel_v6.vif_index_to_name_dic[interface_id]

    @staticmethod
    def get_interface(kernel_tree, interface_id):
        """
        Get PIM interface from interface id
        """
        interface_name = kernel_tree.get_interface_name(interface_id)
        return Main.interfaces_v6.get(interface_name, None)

    @staticmethod
    def get_membership_interface(kernel_tree, interface_id):
        """
        Get MLD interface from interface id
        """
        interface_name = kernel_tree.get_interface_name(interface_id)
        return Main.mld_interfaces.get(interface_name, None)  # type: InterfaceMLD

    @staticmethod
    def get_kernel():
        """
        Get kernel
        """
        return Main.kernel_v6
