# Multirouter

(needs a better name)

Created by Tabor Kvasnicka.

University of Tulsa.

3/17/2021.

A tool for configuring multiple routers from a single command line. It could be used to configure any server with SSH available simultaneously, but it's designed with IPTables in mind.

## Requirements

Needs Python 3.8+. Mostly requires Parallel SSH. Just install the `requirements.txt` with pip:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python src\run.py [load file]
```

You can run src\run.py however you feel like, but that's how I use it. Just note that `run.py` is the "driver."

It should be fairly straightforward to use. You can type `help` at any time for docs on all commands.

## Load File

The load file is just JSON. It holds the information to connect to a set of hosts. You can also add hosts using the REPL, but it's faster this way, especially if you will be reconnecting semi-often.

Example:

Port is optional. The default is 22. The ssh key is optional and only needed if you need it for SSH. The password is always required because IPTables configuration requires sudo which requires authentication. (Note running as root is not supported. And you shouldn't be SSHing as root anyway.)

```json
{
    "hosts": [
        {
            "host": "10.10.10.10",
            "user": "example",
            "password": "ExamplePassword",
            "port": 2222,
            "sshkey": "path/to/ssh/key.pem"
        },
        {
            "host": "10.10.10.11",
            "user": "example2",
            "password": "ExampleP4ssword"
        }
    ]
}
```

## Commands

Note that these are all documented in the `help` menu in the tool as well.

### cmd

Runs a command on the hosts in current context (all if context not set)

### hosts

Manages hosts

Pass no arguments to list hosts.

Args:

```bash
add hostname, username, password, port (default: 22), sshkey (if applicable)    - Add host
remove host1, host2, ...        - Remove list of hosts
remove host_index1, host_index2, ...    - Remove list of hosts by indices
```

### tables

Manages the tables currently being listed with `list`

Pass no arguments to list tables

Args:

```bash
add table1, table2, ... - Add tables
remove table1, table2, ... - Remove list of tables
remove table_index1, table_index2, ... - Remove list of tables by indices
```

### list

Lists the current rules in the current context (all if context not set)

Examples:

```bash
list
list 0 1
list 127.0.0.1
list all
list -v
```

Args:

```bash
-v - Verbose
```

### context

Manages the context (the current hosts being acted on by default)

Pass no arguments to show context.

Args:

```bash
set host1, host2, ... - Set context to list of hosts
set index1, index2, ... - Set context to list of host indices
set all - Set context to all hosts
reset - Unsets the context
```

### iptables

Runs iptables commands

Usage if context not set:

```bash
iptables host1 (or index), host2 (or index), ... (iptables args)
iptables all (iptables args)
```

Usage if context set:

```bash
iptables (iptables args)
```

### save

Saves rules in a directory

No argument saves with save_[timestamp]. You can specify the directory name.

### load

Loads the specified directory and applies the rules (if the hosts are connected to)

### exit

Exits