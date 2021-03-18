##################################################################
#
#   Written by Tabor Kvasnicka
#
#   University of Tulsa
#
#   3/17/2021
#
##################################################################

import os

from colorama import Fore, Back, Style


class IPTablesManager(object):
    def __init__(self, ssh_manager, host_map, tables=["filter", "nat"]):
        self.ssh_manager = ssh_manager
        self.host_map = host_map
        self.tables = tables

    def send_sudo_password(self, output):
        for host_out in output:
            host_out.stdin.write(self.host_map.get_password(host_out.host) + "\n")
            host_out.stdin.flush()

    def add_host(self, host):
        self.ssh_manager.add_host(host)
        self.host_map[host.host] = host

    def remove_hosts(self, hosts):
        self.host_map.remove(hosts)
        self.ssh_manager.remove_hosts(hosts)

    def remove_hosts_indices(self, indices):
        shosts = sorted(self.host_map.keys())
        rhosts = list(
            map(lambda x: x[1], filter(lambda x: x[0] in indices, enumerate(shosts)))
        )
        self.remove_hosts(rhosts)

    def save(self, d):
        c = "&&".join(
            [
                f'printf "\\n{table}\\n" && iptables -S -t{table}'
                for table in self.tables
            ]
        )
        hosts = self.ssh_manager.hosts
        if not self.ssh_manager.context_changed:
            output = self.ssh_manager.run_command(c, sudo=True)
        else:
            ahosts = self.ssh_manager.all_hosts
            cs = [c if h in hosts else "" for h in ahosts]
            output = self.ssh_manager.run_command("%s", commands=cs, sudo=True)
        self.send_sudo_password(output)
        self.ssh_manager.join(output)
        out = []
        for host_out in output:
            if host_out.host not in hosts:
                continue
            lines = [f"{line}\n" for line in host_out.stdout]
            with open(os.path.join(d, f"{host_out.host}.txt"), "w") as f:
                f.writelines(lines)

    def read_commands(self, fn):
        with open(fn, "r") as f:
            s = f.read()

        tables = list(
            map(
                lambda t: list(filter(lambda line: line.strip() != "", t.split("\n"))),
                s.split("\n\n"),
            )
        )
        # print(tables)
        c = []

        for t in tables:
            table = t[0]
            c.append(f"iptables -t {table} -F")
            c.append(" && ".join([f"iptables -t {table} {r}" for r in t[1:]]))

        return " && ".join(c)

    def run_command(self, cmd, sudo=False):
        hosts = self.ssh_manager.hosts
        if not self.ssh_manager.context_changed:
            output = self.ssh_manager.run_command(cmd, sudo=sudo)
        else:
            ahosts = self.ssh_manager.all_hosts
            cs = [cmd if h in hosts else "" for h in ahosts]
            output = self.ssh_manager.run_command("%s", commands=cs, sudo=sudo)
        if sudo:
            self.send_sudo_password(output)
        self.ssh_manager.join(output)
        out = []
        for host_out in output:
            if host_out.host not in hosts:
                continue
            o = "\n".join(host_out.stdout)
            out.append((self.host_map[host_out.host], o))
        out = sorted(out, key=lambda x: x[0].host)
        for host, o in out:
            print("\n" + host.colorize())
            print(o + "\n")

    def load(self, fs):
        ahosts = self.ssh_manager.all_hosts
        c = [""] * len(ahosts)
        hosts = []
        for h, fn in fs.items():
            if h not in ahosts:
                continue
            hosts.append(h)
            i = ahosts.index(h)
            c[i] = self.read_commands(fn)
        ans = input(
            "\nAre you absolutely sure you know what you're doing?\nThis could lock you out.\nType `COMMIT` to proceed: "
        )
        if ans == "COMMIT":
            output = self.ssh_manager.run_command("%s", commands=c, sudo=True)
            self.send_sudo_password(output)
            self.ssh_manager.join(output)
            out = []
            for host_out in output:
                if host_out.host not in hosts:
                    continue
                o = IPTablesManager._colorize("\n".join(host_out.stdout))
                out.append((self.host_map[host_out.host], o))
            out = sorted(out, key=lambda x: x[0].host)
            for host, o in out:
                print("\n" + host.colorize())
                print(o + "\n")
        else:
            print("\nNo worries. Better safe than sorry.\n")

    def list_rules(self, verbose):
        c = "&&".join(
            [
                f'printf "\\n{Fore.YELLOW + table + Style.RESET_ALL}\\n" && iptables -L -t{table} --line-numbers{" -v" if verbose else ""}'
                for table in self.tables
            ]
        )
        hosts = self.ssh_manager.hosts
        if not self.ssh_manager.context_changed:
            output = self.ssh_manager.run_command(c, sudo=True)
        else:
            ahosts = self.ssh_manager.all_hosts
            cs = [c if h in hosts else "" for h in ahosts]
            output = self.ssh_manager.run_command("%s", commands=cs, sudo=True)
        self.send_sudo_password(output)
        self.ssh_manager.join(output)
        out = []
        for host_out in output:
            if host_out.host not in hosts:
                continue
            o = IPTablesManager._colorize("\n".join(host_out.stdout))
            out.append((self.host_map[host_out.host], o))
        out = sorted(out, key=lambda x: x[0].host)
        for host, o in out:
            print("\n" + host.colorize())
            print(o + "\n")

    def list_rules_hosts(self, hosts, verbose):
        c = "&&".join(
            [
                f'printf "\\n{Fore.YELLOW + table + Style.RESET_ALL}\\n" && iptables -L -t{table} --line-numbers{" -v" if verbose else ""}'
                for table in self.tables
            ]
        )
        if not self.ssh_manager.context_changed:
            chosts = self.ssh_manager.hosts
            cs = [c if h in hosts else "" for h in chosts]
        else:
            ahosts = self.ssh_manager.all_hosts
            chosts = self.ssh_manager.hosts
            cs = [c if h in hosts and h in chosts else "" for h in ahosts]
        output = self.ssh_manager.run_command("%s", commands=cs, sudo=True)
        self.send_sudo_password(output)
        self.ssh_manager.join(output)
        out = []
        for host_out in output:
            if host_out.host not in hosts:
                continue
            o = IPTablesManager._colorize("\n".join(host_out.stdout))
            out.append((self.host_map[host_out.host], o))
        out = sorted(out, key=lambda x: x[0].host)
        for host, o in out:
            print("\n" + host.colorize())
            print(o + "\n")

    def list_rules_indices(self, indices, verbose):
        c = "&&".join(
            [
                f'printf "\\n{Fore.YELLOW + table + Style.RESET_ALL}\\n" && iptables -L -t{table} --line-numbers{" -v" if verbose else ""}'
                for table in self.tables
            ]
        )
        if not self.ssh_manager.context_changed:
            shosts = self.ssh_manager.hosts
            hosts = []
            for i in range(len(shosts)):
                if i in indices:
                    hosts.append(shosts[i])
            cs = [c if h in hosts else "" for h in shosts]
        else:
            ahosts = self.ssh_manager.all_hosts
            shosts = self.ssh_manager.hosts
            hosts = []
            for i in range(len(shosts)):
                if i in indices:
                    hosts.append(shosts[i])
            cs = [c if h in hosts else "" for h in ahosts]
        output = self.ssh_manager.run_command("%s", commands=cs, sudo=True)
        self.send_sudo_password(output)
        self.ssh_manager.join(output)
        out = []
        for host_out in output:
            if host_out.host not in hosts:
                continue
            o = IPTablesManager._colorize("\n".join(host_out.stdout))
            out.append((self.host_map[host_out.host], o))
        out = sorted(out, key=lambda x: x[0].host)
        for host, o in out:
            print("\n" + host.colorize())
            print(o + "\n")

    def run_iptables(self, arg, hosts=None, indices=None, all_hosts=False):
        c = f"iptables {arg}"
        ahosts = self.ssh_manager.all_hosts
        if all_hosts:
            hosts = ahosts
        elif hosts is None and indices is None:
            hosts = self.ssh_manager.hosts
        elif hosts is None:
            indices = sorted(list(set(indices)))
            if indices[0] < 0 or indices[len(indices) - 1] >= len(ahosts):
                print("Args invalid")
                return
            hosts = [ahosts[i] for i in indices]
        else:
            hosts = sorted(list(set(hosts)))
        cs = [c if h in hosts else "" for h in ahosts]
        output = self.ssh_manager.run_command("%s", commands=cs, sudo=True)
        self.send_sudo_password(output)
        self.ssh_manager.join(output)
        out = []
        for host_out in output:
            if host_out.host not in hosts:
                continue
            o = IPTablesManager._colorize("\n".join(host_out.stdout))
            out.append((self.host_map[host_out.host], o))
        out = sorted(out, key=lambda x: x[0].host)
        for host, o in out:
            print("\n" + host.colorize())
            print(o + "\n")

    def add_tables(self, tables):
        tables = list(filter(lambda t: t not in self.tables, tables))
        if len(tables) != 0:
            self.tables += tables

    def remove_tables(self, tables):
        table_filter = []
        for t in tables:
            try:
                ti = int(t)
                if ti >= 0 and ti < len(self.tables):
                    table_filter.append(self.tables[ti])
            except ValueError:
                table_filter.append(t)
        self.tables = list(filter(lambda t: t not in table_filter, self.tables))

    def change_context_hosts_all(self):
        self.ssh_manager.change_context_hosts_all()

    def change_context_hosts(self, new_hosts):
        self.ssh_manager.change_context_hosts(new_hosts)

    def change_context_indices(self, indices):
        self.ssh_manager.change_context_indices(indices)

    def reset_context(self):
        self.ssh_manager.reset_context()

    def context_changed(self):
        return self.ssh_manager.context_changed

    def print_context(self):
        hosts = self.ssh_manager.hosts
        if self.context_changed():
            print("\nContext:\n")
            for i in range(len(hosts)):
                print(f"{i}\t{hosts[i]}")
            print()
        else:
            print("\nContext not set\n")

    def print_hosts(self):
        hosts = self.ssh_manager.all_hosts
        print("\nHosts:\n")
        for i in range(len(hosts)):
            print(f"{i}\t{hosts[i]}")
        print()

    def print_tables(self):
        print("\nTables:\n")
        for i in range(len(self.tables)):
            print(f"{i}\t{self.tables[i]}")
        print()

    @staticmethod
    def _colorize(output):
        return (
            output.replace("ACCEPT", Fore.GREEN + "ACCEPT" + Style.RESET_ALL)
            .replace("DENY", Fore.RED + "DENY" + Style.RESET_ALL)
            .replace("DROP", Fore.RED + "DENY" + Style.RESET_ALL)
        )
