from abc import ABCMeta, abstractmethod


class LocalMembershipStateABC(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def has_members():
        raise NotImplementedError


class NoInfo(LocalMembershipStateABC):
    @staticmethod
    def has_members():
        return False


class Include(LocalMembershipStateABC):
    @staticmethod
    def has_members():
        return True


class LocalMembership():
    NoInfo = NoInfo()
    Include = Include()