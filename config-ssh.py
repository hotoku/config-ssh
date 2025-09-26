#!/usr/bin/env python

import logging
import sys
from dataclasses import dataclass

is_debug = "--debug" in sys.argv or "-d" in sys.argv

logging.basicConfig(
    level=logging.DEBUG if is_debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

LOGGER = logging.getLogger(__name__)

files = ["/home/hotoku/.ssh/config", "/mnt/c/Users/Horikoshi_Yasunori/.ssh/config"]


class Block:
    pass


@dataclass
class CommentBlock(Block):
    lines: list[str]


@dataclass
class HostBlock(Block):
    host: str
    lines: list[str]


def parse_args() -> list[str]:
    ret = []
    for arg in sys.argv:
        if arg[0] == "-":
            continue
        ret.append(arg)
    return ret


def read_comment_block(start_pos: int, lines: list[str]) -> tuple[CommentBlock, int]:
    ret = []
    for pos in range(start_pos, len(lines)):
        line = lines[pos]
        if line.strip().startswith("#"):
            ret.append(line)
            continue
        break
    return CommentBlock(lines=ret), pos


def parse_ssh_config(file_path: str) -> list[Block]:
    lines = [l for l in open(file_path).read().split("\n")]
    ret = []
    while pos < len(lines):
        line = lines[pos]
        if line.strip() == "":
            pos += 1
            continue
        if line.strip().startswith("#"):
            comment_block, next_pos = read_comment_block(pos, lines)
            ret.append(comment_block)
            pos = next_pos
            continue
        if line.strip().lower().startswith("host "):
            host = line.strip()[5:].strip()
            ret.append(HostBlock(host=host, lines=[line]))
            continue
        if len(ret) == 0:
            LOGGER.warning("Ignoring line outside of any block: %s", line)
            continue
        ret[-1].lines.append(line)


def main():
    args = parse_args()
    assert len(args) == 2, "Please specify exactly two arguments."
    instance_name = args[0]
    alias_name = args[1]

    for file in files:
        LOGGER.debug("Processing SSH config file: %s", file)
        config_lines = parse_ssh_config(file)
        for line in config_lines:
            LOGGER.debug("Config Line: %s", line)


if __name__ == "__main__":
    main()
