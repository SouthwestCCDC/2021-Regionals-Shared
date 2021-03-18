##################################################################
#
#   Written by Tabor Kvasnicka
#
#   University of Tulsa
#
#   3/17/2021
#
##################################################################

import cmd, sys, socket, os, time

if os.name == "nt":
    from pyreadline import Readline

    readline = Readline()
else:
    import readline

from .ssh_handler import SSHManager
from .host import *


class MultirouterShell(cmd.Cmd):
    """REPL for handling multiple routers"""

    intro = "Welcome to Multirouter, the tool designed to configure multiple IPTables routers via SSH.\n"
    prompt = "> "

    def __init__(self, iptables_manager):
        self.iptables_manager = iptables_manager

        super().__init__()

    def emptyline(self):
        return

    def do_EOF(self, arg):
        """Handles the EOF signal"""
        print("\n\n")
        sys.exit(0)

    def do_cmd(self, arg):
        """Runs a command on the hosts in current context (all if context not set)"""
        args = parse(arg)
        if len(args) == 0:
            return

        sudo = bool(args[0] == "sudo")
        if sudo:
            self.iptables_manager.run_command(" ".join(args[1:]), sudo=True)
        else:
            self.iptables_manager.run_command(" ".join(args))

    def do_hosts(self, arg):
        """Manages hosts

        Pass no arguments to list hosts.

        Args:

        add hostname, username, password, port (default: 22), sshkey (if applicable)\tAdd host
        remove host1, host2, ...\t\tRemove list of hosts
        remove host_index1, host_index2, ...\tRemove list of hosts by indices
        """
        args = parse(arg)
        if len(args) == 0:
            self.iptables_manager.print_hosts()
        elif len(args) > 1:
            if args[0] == "add":
                if len(args) not in (4, 5, 6):
                    print("Args invalid")
                else:
                    hostname = args[1]
                    user = args[2]
                    password = args[3]
                    port = 22
                    sshkey = None
                    if len(args) > 4:
                        try:
                            p = int(args[4])
                            port = p
                        except ValueError:
                            if len(args) > 5:
                                print("Args invalid")
                                return
                            sshkey = args[4]
                    elif len(args) > 5:
                        sshkey = args[5]
                    creds = Credential(user, password, sshkey)
                    host = Host(hostname, creds, port)
                    self.iptables_manager.add_host(host)
                    self.iptables_manager.print_hosts()
            elif args[0] == "remove":
                status, args = validate_args(args[1:])
                if status == 0:
                    print("Args invalid")
                elif status == 1:
                    self.iptables_manager.remove_hosts(args)
                    self.iptables_manager.print_hosts()
                elif status == 2:
                    self.iptables_manager.remove_hosts_indices(args)
                    self.iptables_manager.print_hosts()
            else:
                print("Args invalid")
        else:
            print("Args invalid")

    def do_tables(self, arg):
        """Manages the tables currently being listed with `list`

        Pass no arguments to list tables

        Args:

        add table1, table2, ...\t\t\tAdd tables
        remove table1, table2, ...\t\tRemove list of tables
        remove table_index1, table_index2, ...\tRemove list of tables by indices
        """
        args = parse(arg)
        if len(args) == 0:
            self.iptables_manager.print_tables()
        elif len(args) > 1:
            if args[0] == "add":
                self.iptables_manager.add_tables(args[1:])
                self.iptables_manager.print_tables()
            elif args[0] == "remove":
                self.iptables_manager.remove_tables(args[1:])
                self.iptables_manager.print_tables()
            else:
                print("Args invalid")

    def do_list(self, arg):
        """Lists the current rules in the current context (all if context not set)

        Examples:
        list
        list 0 1
        list 127.0.0.1
        list all
        list -v

        Args:

        -v\tVerbose
        """
        args = parse(arg)
        verbose = "-v" in args
        if verbose:
            args = list(filter(lambda a: a != "-v", args))
        if len(args) == 0 or "all" in args or "a" in args:
            self.iptables_manager.list_rules(verbose)
        else:
            status, args = validate_args(args)
            if status == 0:
                print("Args invalid")
            elif status == 1:
                self.iptables_manager.list_rules_hosts(args, verbose)
            else:
                self.iptables_manager.list_rules_indices(args, verbose)

    def do_context(self, arg):
        """Manages the context (the current hosts being acted on by default)

        Pass no arguments to show context.

        Args:

        set host1, host2, ...\tSet context to list of hosts
        set index1, index2, ...\tSet context to list of host indices
        set all\tSet context to all hosts
        reset\tUnsets the context
        """
        args = parse(arg)
        if len(args) == 0:
            self.iptables_manager.print_context()
        elif len(args) == 1:
            if args[0] == "reset":
                self.iptables_manager.reset_context()
                self.iptables_manager.print_context()
            else:
                print("Args invalid")
        else:
            if args[0] == "set":
                if "all" in args[1:]:
                    self.iptables_manager.change_context_hosts_all()
                    self.iptables_manager.print_context()
                else:
                    status, args = validate_args(args[1:])
                    if status == 0:
                        print("Args invalid")
                    elif status == 1:
                        try:
                            self.iptables_manager.change_context_hosts(args)
                            self.iptables_manager.print_context()
                        except SSHManager.ContextException as e:
                            print(str(e))
                    elif status == 2:
                        try:
                            self.iptables_manager.change_context_indices(args)
                            self.iptables_manager.print_context()
                        except SSHManager.ContextException as e:
                            print(str(e))
            else:
                print("Args invalid")

    def do_iptables(self, arg):
        """Runs iptables commands

        Usage if context not set:
        iptables host1 (or index), host2 (or index), ... (iptables args)
        iptables all (iptables args)

        Usage if context set:
        iptables (iptables args)
        """
        idx = arg.find("-")
        if not self.iptables_manager.context_changed() or (idx > 0):
            if idx == -1:
                return
            args = parse(arg[:idx])
            cmd = arg[idx:]

            if len(args) == 0 and len(self.iptables_manager.host_map) > 1:
                print(
                    "If context not set, you must specify the hosts (either address or number) or 'all'"
                )
            elif len(args) == 0 or "all" in args:
                self.iptables_manager.run_iptables(cmd, all_hosts=True)
            else:
                status, args = validate_args(args)
                if status == 0:
                    print("Args invalid")
                elif status == 1:
                    self.iptables_manager.run_iptables(cmd, hosts=args)
                elif status == 2:
                    self.iptables_manager.run_iptables(cmd, indices=args)
        elif idx != -1:
            self.iptables_manager.run_iptables(arg)

    def do_save(self, arg):
        """Saves rules in a directory

        No argument saves with save_[timestamp]. You can specify the directory name.
        """
        args = parse(arg)
        if len(args) == 0:
            t = time.localtime()
            timestamp = time.strftime("%b-%d-%Y_%H%M", t)
            d = f"save_{timestamp}"
            os.makedirs(d)
            self.iptables_manager.save(d)
        elif len(args) == 1:
            d = args[0]
            try:
                os.makedirs(d)
                self.iptables_manager.save(d)
            except FileExistsError:
                print("Directory already exists")
        else:
            print("Too many args")

    def do_load(self, arg):
        """Loads the specified directory and applies the rules (if the hosts are connected to)"""
        args = parse(arg)
        if len(args) == 0:
            print("Directory name required")
        elif len(args) == 1:
            d = args[0]
            if os.path.exists(d):
                fs = dict(
                    map(
                        lambda f: (f[:-4], os.path.join(d, f)),
                        filter(lambda f: f.endswith(".txt"), os.listdir(d)),
                    )
                )
                ans = input(
                    "WARNING: this operation will reset the tables, but it will NOT change the default policies.\nMake sure you set your policies to accept traffic or you're in for a bad time.\nProceed? (yes/no) "
                )
                while ans != "yes" and ans != "no":
                    print("Answer must be `yes` or `no`")
                    input("Proceed? (yes/no) ")
                if ans == "yes":
                    self.iptables_manager.load(fs)
                elif ans == "no":
                    print("\nGood call\nSee you when you're ready.\n")
        else:
            print("Args invalid")

    def do_exit(self, arg):
        """Exits"""
        sys.exit(0)


def validate_args(args):
    status = 0  # 0 = invalid, 1 = host list, 2 = number list
    args_out = []
    for arg in args:
        try:
            a = int(arg)
            if status == 1:
                return (0, None)
            status = 2
            args_out.append(a)
        except ValueError:
            try:
                socket.inet_aton(arg)
                if status == 2:
                    return (0, None)
                status = 1
                args_out.append(arg)
            except OSError:
                return (0, None)
    return (status, args_out)


def parse(arg):
    return tuple(arg.split())