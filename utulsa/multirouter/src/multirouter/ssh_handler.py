##################################################################
#
#   Written by Tabor Kvasnicka
#
#   University of Tulsa
#
#   3/17/2021
#
##################################################################

from pssh.clients import ParallelSSHClient
from pssh.config import HostConfig

import copy


class HostConfigException(Exception):
    pass


class SSHManager(object):
    context_changed = False

    def __init__(self, hosts, host_config):
        self.hosts = sorted(hosts)
        self.all_hosts = copy.deepcopy(self.hosts)
        self.client = ParallelSSHClient(self.hosts, host_config=host_config)

    def remove_hosts(self, hosts):
        indices = []
        new_hosts = []
        for i in range(len(self.all_hosts)):
            if self.all_hosts[i] in hosts:
                indices.append(i)
            else:
                new_hosts.append(self.all_hosts[i])
        self.all_hosts = new_hosts
        if self.context_changed:
            self.hosts = list(filter(lambda h: h not in hosts, self.hosts))
        else:
            self.hosts = copy.deepcopy(self.all_hosts)
        self.client.host_config = list(
            map(
                lambda x: x[1],
                filter(
                    lambda x: x[0] not in indices, enumerate(self.client.host_config)
                ),
            )
        )
        self.client.hosts = self.all_hosts

    def add_host(self, host):
        self.all_hosts.append(host.host)
        self.all_hosts = sorted(list(set(self.all_hosts)))
        host_configs = self.client.host_config
        idx = self.all_hosts.index(host.host)
        host_configs.insert(idx, host.build_host_config())
        self.client.hosts = self.all_hosts
        self.client.host_config = host_configs
        if not self.context_changed:
            self.hosts = copy.deepcopy(self.all_hosts)

    def run_command(self, command, commands=None, sudo=False):
        if commands is None:
            return self.client.run_command(command, sudo=sudo)
        else:
            return self.client.run_command(command, host_args=commands, sudo=sudo)

    def join(self, output):
        self.client.join(output)

    def change_context_hosts_all(self):
        self.change_context_hosts(self.all_hosts)

    def change_context_hosts(self, new_hosts):
        new_hosts = sorted(list(set(new_hosts)))

        for h in new_hosts:
            if h not in self.all_hosts:
                raise SSHManager.ContextException(f"Host {h} not in host list")

        self.hosts = list(filter(lambda h: h in new_hosts, self.all_hosts))
        self.context_changed = True

    def change_context_indices(self, indices):
        indices = sorted(indices)
        if indices[0] < 0 or indices[len(indices) - 1] >= len(self.all_hosts):
            raise SSHManager.ContextException("Indices out of range")
        new_hosts = []
        for i in indices:
            new_hosts.append(self.all_hosts[i])
        self.change_context_hosts(new_hosts)

    def reset_context(self):
        self.hosts = copy.deepcopy(self.all_hosts)
        self.context_changed = False

    @staticmethod
    def build_host_config(*, n=0, users=None, passwords=None, user=None, password=None):
        if bool(users is None) == bool(user is None):
            raise HostConfigException("Users or User (not both) needs to be defined")
        elif bool(passwords is None) == bool(password is None):
            raise HostConfigException(
                "Passwords or Password (not both) needs to be defined"
            )
        elif passwords != None and len(passwords) != n:
            raise HostConfigException("Length of Passwords != n")
        elif users != None and len(users) != n:
            raise HostConfigException("Length of Users != n")
        elif n <= 0:
            raise HostConfigException("n should be greater than 0")

        if user is None and password is None:
            return [HostConfig(user=users[i], password=passwords[i]) for i in range(n)]
        elif user is None:
            return [HostConfig(user=users[i], password=password) for i in range(n)]
        elif password is None:
            return [HostConfig(user=user, password=password[i]) for i in range(n)]
        else:
            return [HostConfig(user=user, password=password) for i in range(n)]

    class ContextException(Exception):
        pass
