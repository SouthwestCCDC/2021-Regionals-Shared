##################################################################
#
#   Written by Tabor Kvasnicka
#
#   University of Tulsa
#
#   3/17/2021
#
##################################################################

from multirouter.ssh_handler import *
from multirouter.host import *
from multirouter.shell import *
from multirouter.iptables_manager import *
from colorama import Fore, Back, Style, init as cinit

import json, sys, os


def usage(arg):
    print(f"\nUsage:\n{arg} [load file (json)]\n-h, --help\t\tHelp\n")


if __name__ == "__main__":
    try:
        cinit()

        if len(sys.argv) > 2:
            print("Too many args\n")
            usage(sys.argv[0])
            sys.exit(1)

        if len(sys.argv) == 2:
            if sys.argv[1] == "-h" or sys.argv[1] == "--help":
                usage(sys.argv[0])
                sys.exit(0)
            elif os.path.exists(sys.argv[1]):
                f = open(sys.argv[1], "r")
                data = json.load(f)
                hs = sorted(data["hosts"], key=lambda h: h["host"])
                hostnames = list(map(lambda h: h["host"], hs))
                creds = list(
                    map(
                        lambda h: Credential(
                            h["user"],
                            h["password"],
                            h["sshkey"] if "sshkey" in h else None,
                        ),
                        hs,
                    )
                )
                hosts = [
                    Host(
                        hostnames[i],
                        creds[i],
                        port=hs[i]["port"] if "port" in hs[i] else 22,
                    )
                    for i in range(len(hostnames))
                ]
                host_config = [h.build_host_config() for h in hosts]
                host_map = HostMap(hostnames, hosts)
                ssh_manager = SSHManager(hostnames, host_config)

                iptables_manager = IPTablesManager(ssh_manager, host_map)
                MultirouterShell(iptables_manager).cmdloop()
            else:
                print("File doesn't exist")
                sys.exit(1)
        else:
            print("Load file required")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n")
        pass