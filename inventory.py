#!/usr/bin/env python3

import argparse
import os
import re

from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader


def _get_ssh_params(inventory_file_name):
    hosts = {}

    data_loader = DataLoader()
    inventory = InventoryManager(loader=data_loader,
                                 sources=[inventory_file_name])
    for host, val in inventory.hosts.items():
        vars = val.get_vars()
        hosts[host] = {
            "HostName": vars.get("ansible_host", host),
            "Port": vars.get("ansible_port"),
            "Options": vars.get("ansible_ssh_common_args")
        }
    return hosts


def _main(mode, inventory_path, target_client=None):
    clients = {}

    inventory_path_full = os.path.expanduser(inventory_path)
    for root, dirs, files in os.walk(inventory_path_full):
        for name in files:
            basename = os.path.basename(root)
            if (basename not in ["vaults", "vars", "group_vars", "host_vars"]
                    and os.path.splitext(name)[1] in [".yml", ".yaml"]):
                client = root.replace(inventory_path_full,
                                      "").split(os.sep)[0].split("-")[0]
                if mode == "all":
                    clients.setdefault(client, {}).update(
                        _get_ssh_params(os.path.join(root, name)))
                elif mode == "clients_only":
                    clients.setdefault(client, {})
                elif mode == "client_hosts":
                    if client == target_client:
                        clients.setdefault(client, {}).update(
                            _get_ssh_params(os.path.join(root, name)))
    return clients


def _get_flat_hosts(client_hosts):
    flat_list = []
    for sublist in client_hosts.values():
        for item in sublist.keys():
            flat_list.append(item)
    return flat_list


def _replace_ansible_host_with_ip(client_hosts, ssh_opts):
    proxycommand_re = re.compile(r"ProxyCommand=[\"|'](.*)[\"|']")
    host_re = re.compile(r"([a-zA-Z][\w\.-]+)")
    proxycommand = proxycommand_re.findall(ssh_opts)
    if proxycommand:
        host = host_re.findall(proxycommand[0])
        if "ssh" in host:
            host.remove("ssh")
        if host:
            if host[0] in client_hosts:
                ip = client_hosts[host[0]]["HostName"]
                ssh_opts = ssh_opts.replace(host[0], ip)
    return ssh_opts


def get_clients(inventory_path):
    print(" ".join(_main("clients_only", inventory_path).keys()))


def get_hosts_all(inventory_path):
    client_hosts = _main("all", inventory_path)
    print(" ".join(_get_flat_hosts(client_hosts)))


def get_client_hosts(client, inventory_path):
    client_hosts = _main("client_hosts", inventory_path, target_client=client)
    print(" ".join(client_hosts.get(client, {}).keys()))


def get_client_hosts_all(inventory_path):
    client_hosts = _main("all", inventory_path)
    clients = client_hosts.keys()
    hosts = _get_flat_hosts(client_hosts)
    print(" ".join(list(clients) + hosts))


def get_ssh_string(host, inventory_path, client=None, quote_opts_quotes=False):
    if client:
        client_hosts = _main("client_hosts",
                             inventory_path,
                             target_client=client)[client]
    else:
        client_hosts = {}
        for hosts in _main("all", inventory_path).values():
            client_hosts.update(hosts)
    host_vars = client_hosts.get(host)
    if host_vars:
        port_str = ("-p " +
                    str(host_vars["Port"]) if host_vars["Port"] else None)
        ssh_opts = host_vars["Options"]
        if host_vars["Options"]:
            ssh_opts = _replace_ansible_host_with_ip(client_hosts, ssh_opts)

            if quote_opts_quotes:
                ssh_opts = re.sub('("[^"]+")', r"'\g<1>'",
                                  ssh_opts.replace("'", '"'))

        ssh_args = [
            x for x in [port_str, ssh_opts, host_vars['HostName']] if x
        ]
        ssh_str = f"{' '.join(ssh_args)}"

        print(ssh_str)


def config_update(config_main, config_dir, inventory_path, client=None):
    config_dir_full = os.path.expanduser(config_dir)
    if not os.path.isdir(config_dir_full):
        try:
            os.mkdir(config_dir_full, 0o700)
        except OSError:
            print(f"Directory creation failed: {config_dir_full}")

    if client:
        client_hosts = _main("client_hosts",
                             inventory_path,
                             target_client=client)
    else:
        client_hosts = _main("all", inventory_path)

    for client, hosts in client_hosts.items():
        config_lines = {}
        print(f"{client}: {len(hosts)} hosts")
        for host, host_vars in hosts.items():
            lines = [f"Host {host}"]
            print(f"{client}: adding {host} with {host_vars}")
            for param, value in host_vars.items():
                if value:
                    lines.append(f"  {param} {value}")
            if len(lines) > 1:
                config_lines[host] = lines.copy()

        client_ssh_conf = os.path.join(config_dir_full, client)
        with open(client_ssh_conf, "w") as f:
            for host, val in config_lines.items():
                f.writelines([x + "\n" for x in val])
                f.write("\n")
        os.chmod(client_ssh_conf, 0o600)

    config_main_full = os.path.expanduser(config_main)

    relative_dir_path = os.path.relpath(config_dir_full,
                                        os.path.dirname(config_main_full))
    option = f"Include {relative_dir_path}/*"
    with open(config_main_full, "r") as f:
        ssh_config_conts = f.readlines()

    if option not in [x.rstrip() for x in ssh_config_conts]:
        print(f"Adding '{option}' to {config_main}")
        with open(config_main_full, "w") as f:
            f.write(option + "\n\n")
            f.writelines(ssh_config_conts)


def _argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory",
                        help="Path to ansible inventory",
                        required=True)
    parser.add_argument("--client", help="Search in client hosts only")
    parser.add_argument("--config-dir",
                        help="Path to the ssh clients config dir",
                        default="~/.ssh/config.d/")
    parser.add_argument("--config-main",
                        help="Path to the main ssh config",
                        default="~/.ssh/config")
    # workaround for xxh
    parser.add_argument("--quote-opts-quotes",
                        help="Place quoted ssh options in quotes",
                        action="store_true")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--string", help="Get ssh string")
    group.add_argument("--config",
                       help="Update ssh configs",
                       action="store_true")
    group.add_argument("--completion",
                       help="Get hosts completion",
                       choices=["hosts", "clients", "both"])
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = _argparser()

    if not os.path.exists(args.inventory):
        raise FileNotFoundError(f"{args.inventory} does not exist!")

    if args.completion:
        if args.completion == "hosts":
            if args.client:
                get_client_hosts(args.client, args.inventory)
            else:
                get_hosts_all(args.inventory)
        elif args.completion == "clients":
            get_clients(args.inventory)
        elif args.completion == "both":
            get_client_hosts_all(args.inventory)
    elif args.string:
        get_ssh_string(args.string, args.inventory, args.client,
                       args.quote_opts_quotes)
    elif args.config:
        config_update(args.config_main, args.config_dir, args.inventory,
                      args.client)
