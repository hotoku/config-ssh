#!/usr/bin/env python

import logging
import sys
from dataclasses import dataclass

IS_DEBUG = "--debug" in sys.argv or "-d" in sys.argv
LOGGER = logging.getLogger(__name__)
WSL_CONFIG, WIN_CONFIG = [
    "/home/hotoku/.ssh/config",
    "/mnt/c/Users/Horikoshi_Yasunori/.ssh/config",
]


logging.basicConfig(
    level=logging.DEBUG if IS_DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@dataclass
class HeaderBlock:
    lines: list[str]


@dataclass
class HostBlock:
    host: str
    hostname: str
    pos: int  # HostName line position in the block
    lines: list[str]


type Block = HeaderBlock | HostBlock


def parse_args() -> list[str]:
    ret = []
    for arg in sys.argv[1:]:  # Skip the script name
        if arg[0] == "-":
            continue
        ret.append(arg)
    return ret


def parse_header_block(lines: list[str]) -> tuple[HeaderBlock, list[str]]:
    def is_end():
        return len(lines) == 0 or lines[0].strip().lower().startswith("host ")

    header_lines = []
    while not is_end():
        header_lines.append(lines.pop(0))
    return HeaderBlock(lines=header_lines), lines


def parse_host_block(lines: list[str]) -> tuple[HostBlock, list[str]]:
    def is_end():
        return len(lines) == 0 or lines[0].strip().lower().startswith("host ")

    host_line = lines.pop(0).strip()
    key, value = host_line[:4], host_line[4:].strip()
    assert key.lower() == "host", f"Expected 'Host' line, got: {host_line}"
    host = value
    host_lines = [host_line]
    pos = 0
    hostname = ""
    while not is_end():
        pos += 1
        cur_line = lines.pop(0)
        host_lines.append(cur_line)
        if cur_line.strip().lower().startswith("hostname "):
            _, hostname = cur_line.strip().split(" ", 1)
            retpos = pos
    assert hostname != "", f"'Hostname' not found in host block for '{host}'"
    return HostBlock(host=host, hostname=hostname, pos=retpos, lines=host_lines), lines


def parse_ssh_config(file_path: str) -> list[Block]:
    lines = [l for l in open(file_path).read().split("\n")]
    ret = []
    header, lines = parse_header_block(lines)
    ret.append(header)
    while len(lines) > 0:
        host_block, lines = parse_host_block(lines)
        ret.append(host_block)
    return ret


def search_entry(block: HostBlock, key: str) -> str | None:
    for line in block.lines:
        if line.strip().lower().startswith(key.lower()):
            return line
    raise ValueError(f"Key '{key}' not found in block.")


def search_host(name: str, blocks: list[Block]) -> HostBlock:
    for block in blocks:
        if isinstance(block, HostBlock) and block.host == name:
            return block
    raise ValueError(f"Host '{name}' not found.")


def update_hostname(block: HostBlock, new_hostname: str) -> None:
    old_line = block.lines[block.pos]
    prefix = ""
    for c in old_line:
        if c.isspace():
            prefix += c
        else:
            break
    block.lines[block.pos] = f"{prefix}HostName {new_hostname}"


def write_ssh_config(file_path: str, blocks: list[Block]) -> None:
    with open(file_path, "w") as f:
        for block in blocks:
            for line in block.lines:
                f.write(line + "\n")


def update_wsl(wsl_config: str, instance_name: str, alias_name: str) -> str:
    blocks = parse_ssh_config(wsl_config)
    host_block = search_host(instance_name, blocks)
    hostname = host_block.hostname
    alias_block = search_host(alias_name, blocks)
    update_hostname(alias_block, hostname)
    write_ssh_config(wsl_config, blocks)
    return hostname


def update_windows(win_config: str, alias_name: str, hostname: str) -> None:
    blocks = parse_ssh_config(win_config)
    host_block = search_host(alias_name, blocks)
    update_hostname(host_block, hostname)
    write_ssh_config(win_config, blocks)


def main():
    args = parse_args()
    assert len(args) == 2, "Please specify exactly two arguments."
    instance_name = args[0]
    alias_name = args[1]

    hostname = update_wsl(WSL_CONFIG, instance_name, alias_name)
    update_windows(WIN_CONFIG, alias_name, hostname)


if __name__ == "__main__":
    main()
