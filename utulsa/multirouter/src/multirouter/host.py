##################################################################
#
#   Written by Tabor Kvasnicka
#
#   University of Tulsa
#
#   3/17/2021
#
##################################################################

from pssh.config import HostConfig
from colorama import Fore, Back, Style


class Credential(object):
    """Holds the credentials"""

    user = None
    password = None
    sshkey = None

    def __init__(self, user, password, sshkey=None):
        """Initializes Credentials

        Args:
            user (str): The user to connect as
            password (str): Password to use. Defaults to None.
            sshkey (str, optional): Path to ssh private key file (if used). Defaults to None.
        """

        self.user = user
        self.password = password
        self.sshkey = sshkey

    def uses_ssh_key(self):
        """Checks if the host is using an ssh key

        Returns:
            bool: Whether SSH key is being used
        """
        return self.sshkey is not None


class Host(object):
    """Holds the Host information"""

    def __init__(self, host, cred, port=22):
        """Initializes Host

        Args:
            host (str): Host name / address
            cred (Credential): Credentials object to log in
            port (int, optional): Port to connect to via SSH. Defaults to 22.
        """
        self.host = host
        self.cred = cred
        self.port = port

    def build_host_config(self):
        """Builds Host config for Parallel SSH

        Returns:
            HostConfig: HostConfig for SSH
        """
        if self.cred.uses_ssh_key():
            return HostConfig(
                port=self.port,
                user=self.cred.user,
                password=self.cred.password,
                private_key=self.cred.sshkey,
            )
        else:
            return HostConfig(
                port=self.port, user=self.cred.user, password=self.cred.password
            )

    def colorize(self):
        """Returns a colorized hostname

        Returns:
            str: Colorized hostname
        """
        return Fore.BLACK + Back.WHITE + self.host + Style.RESET_ALL


class HostMap(object):
    """Maps host name to the rest of the information"""

    def __init__(self, hostnames, hosts):
        """Initializes hostmap

        Args:
            hostnames ([str]): List of hostnames
            hosts ([Host]): List of Host objects
        """
        self.hostmap = dict(zip(hostnames, hosts))

    def __len__(self):
        """Gets the number of items in host map

        Returns:
            int: Number of items in host map
        """
        return len(self.hostmap)

    def __getitem__(self, hostname):
        """Gets the corresponding Host object

        Args:
            hostname (str): Hostname

        Returns:
            Host: Host object
        """
        return self.hostmap[hostname]

    def __setitem__(self, hostname, host):
        """Sets the item in the host map

        Args:
            hostname (str): Host name
            host (Host): Host object
        """
        self.hostmap[hostname] = host

    def keys(self):
        """Gets a list of hostnames

        Returns:
            [str]: List of hostnames
        """
        return self.hostmap.keys()

    def get_password(self, hostname):
        """Gets the password for a host

        Args:
            hostname (str): Host name

        Returns:
            str: Password
        """
        return self.hostmap[hostname].cred.password

    def remove(self, hosts):
        """Removes a list of hosts from the hostmap

        Args:
            hosts ([str]): List of host names to remove
        """
        self.hostmap = dict(filter(lambda h: h[0] not in hosts, self.hostmap.items()))

    def print_hosts(self):
        """Prints the host names"""
        hostnames = list(self.hostmap.keys())
        hostnames.sort()
        for host in hostnames:
            print(host)