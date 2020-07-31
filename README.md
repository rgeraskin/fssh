# f(arce)ssh

`fssh` will help if you
* are on support with many clients with a lot of servers
* have ansible inventory for them
* tired to grep it all the time to get ssh connection params

`fssh` parses ansible inventory and produces connection-ready ssh command on-the-fly. Under the hood it is a simple zsh autocomplete function and python script.

Also `fssh` could be used without zsh to generate ssh configs based on ansible host settings.

## Demo

![demo](./demo.svg)

> Notice that two usage approaches are demonstrated here together. But you could choose the only one at the time.

## Install

### Manually
Installation process for `oh-my-zsh`

1. Clone repo to plugins dir
   ```bash
   $ git clone https://github.com/roman-geraskin/fssh.git ~/.oh-my-zsh/custom/plugins/fssh
   ```
1. Add `fssh` plugin
    ```
    plugins=(... fssh)
    ```

## Configure

1. Specify required settings in `~/.zshrc`
    ```
    FSSH_INVENTORY=~/path/to/ansible/inventories/
    ```

## Requirements

- [ohmyzsh](https://github.com/ohmyzsh/ohmyzsh) (honestly I didn't try `fssh` without it)
- ansible (python3 libs are required)
- ansible inventory directory layout should look like this:
  ```
  ➜  inventories git:(master) tree .
  .
  ├── client1-cloud
  │   ├── group_vars
  │   ├── hosts.yaml
  │   ├── vars
  │   └── vaults
  ├── client1-office
  │   └── inventory.yaml
  ├── client2
  │   └── inv.yml
  ├── client3-gilfoyle
  │   ├── hosts.yaml
  │   ├── vars
  │   │   └── users.yml
  │   └── vaults
  │       └── user_passwords.yml
  ...
  ```

## Usage

For example, client3-gilfoyle ansible inventory `hosts.yaml` is:
```
all:
  children:
    hw_hosts:
      hosts:
        anton:
          ansible_host: 164.90.189.27
          ansible_port: 1337
          private_addr: 192.168.20.1
    vm_hosts:
      hosts:
        hosting:
          ansible_host: 195.13.48.18
          ansible_port: 2198
          private_addr: 192.168.20.4
        db:
          ansible_host: 91.153.94.128
          ansible_port: 2206
          private_addr: 192.168.20.5
        backup:
          ansible_host: 94.13.184.18
          ansible_port: 2206
          private_addr: 192.168.20.8
        dev.google.com:
          ansible_host: 94.13.185.18
          ansible_port: 2213
          private_addr: 192.168.20.11
```
### SSH using client name and ansible hostname

1. Autocomplete clients
   ```
   ➜  ~ fssh <TAB>
   client1  client2  client3
   ```
1. Autocomplete hosts
   ```
   ➜  ~ fssh client3 <TAB>
   anton           backup          db              dev.google.com  hosting
   ```
1. Get ssh connection string
   ```
   ➜  ~ fssh client3 anton<ENTER>
   Composing host string...
   ➜  ~ ssh -p 1337 164.90.189.27 # anton
   ```
   All you need is to press <ENTER> again to connect to `anton`.

### SSH using ansible hostname only

You should add `FSSH_COMPLETION=both` setting to `~/.zshrc` to connect this way. If you have a lot of inventories this approach will be slower.

1. Autocomplete host or client
   ```
   ➜  ~ fssh <TAB>
   anton                  client1                client1.mars           client1.saturn         client2                dev.google.com            mMonica.piedpiper.net
   backup                 client1.earth          client1.mercury        client1.uranus         client3                dinesh.piedpiper.net      nelson.piedpiper.net
   bertram.piedpiper.net  client1.jupiter        client1.neptune        client1.venus          db                     hosting                   richard.piedpiper.net
   ```
   All client names and all hosts are provided by completion. You could choose any but now we try host-only approach.
1. Choose host
   ```
   ➜  ~ fssh richard.piedpiper.net<ENTER>
   Composing host string...
   ➜  ~ ssh -p 22313 164.90.189.27 # richard.piedpiper.net
   ```
   Press <ENTER> again to connect to `richard.piedpiper.net`.

### Generate ssh configs from ansible inventory
1. Launch `inventory.py` manually
   ```
   ➜  ~ ~/.oh-my-zsh/custom/plugins/fssh/inventory.py --inventory ~/path/to/ansible/inventories/ --config
   client1: 8 hosts
   client1: adding client1.mercury with {'HostName': '182.129.122.3', 'Port': None}
   client1: adding client1.venus with {'HostName': '192.80.182.7', 'Port': None}
   client1: adding client1.earth with {'HostName': '145.136.187.81', 'Port': None}
   client1: adding client1.mars with {'HostName': '158.51.252.217', 'Port': None}
   client1: adding client1.jupiter with {'HostName': '148.159.80.31', 'Port': None}
   client1: adding client1.neptune with {'HostName': '191.12.176.190', 'Port': 2202}
   client1: adding client1.saturn with {'HostName': '23.219.127.255', 'Port': 9113}
   client1: adding client1.uranus with {'HostName': '214.187.204.158', 'Port': 24}
   client2: 5 hosts
   client2: adding richard.piedpiper.net with {'HostName': '164.90.189.27', 'Port': 22}
   client2: adding nelson.piedpiper.net with {'HostName': '135.138.103.8', 'Port': 22321}
   client2: adding bertram.piedpiper.net with {'HostName': '86.146.238.196', 'Port': 2236}
   client2: adding dinesh.piedpiper.net with {'HostName': '12.1.131.212', 'Port': 22320}
   client2: adding mMonica.piedpiper.net with {'HostName': '77.239.86.127', 'Port': 22322}
   client3: 5 hosts
   client3: adding anton with {'HostName': '164.90.189.27', 'Port': 22}
   client3: adding hosting with {'HostName': '106.99.146.61', 'Port': 2213}
   client3: adding db with {'HostName': '95.143.103.136', 'Port': 2215}
   client3: adding backup with {'HostName': '20.125.112.216', 'Port': 2223}
   client3: adding dev.google.com with {'HostName': '78.230.130.101', 'Port': 2227}
   Adding 'Include config.d/*' to ~/.ssh/config
   ```
   SSH configs will be generated for every client in `~/.ssh/config.d/`. Also `Include config.d/*` option will be added to `~/.ssh/config` to guide ssh to client configs.

   To support this your ssh client should be recent enough.

1. Now you could connect to the hosts using ssh only. Autocompletion works too!
   ```
   ➜  ~ ssh richard.piedpiper.net
   Welcome to Ubuntu 18.04.3 LTS (GNU/Linux 4.15.0-66-generic x86_64)
   ```
   Don't forget to run the script again on inventory updates.

## Issues

- Only `ansible_host` and `ansible_port` options are supported for now.
- `Jumphost` aka `ProxyCommand` aka `ansible_ssh_common_args` functionality is missing too. It'll be implemented it in the next releases firstly.

PR are welcome!

## License

The application is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).