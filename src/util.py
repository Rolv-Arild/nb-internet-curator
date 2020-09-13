import os
import re
import json
from collections import namedtuple
from pathlib import Path

import warcio

def load_config():
    pth = Path(__file__).parent.parent.absolute() / "config.json"
    config = json.load(open(pth))
    return namedtuple("Config", ["working_directory", "arc_source_directory", "result_directory"])(**config)


CONFIG = load_config()


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def find_arcs(folder, max_size=2 ** 33):
    for file in os.listdir(folder):
        pth = f"{folder}/{file}"
        if os.path.isdir(pth):
            for pth in find_arcs(pth):
                max_size -= os.path.getsize(pth)
                if max_size < 0:
                    return
                yield pth
        elif os.path.isfile(pth) and "arc" in file:
            max_size -= os.path.getsize(pth)
            if max_size < 0:
                return
            yield pth


def iter_record(arc_path):
    with open(arc_path, "rb") as stream:
        for record in warcio.archiveiterator.ARCIterator(stream):
            yield record


def is_root(record, reg=None):
    if reg is None:
        reg = r"^https?:\/\/[\w.]+no(:\d+)?\/?$"
    if record.content_type == 'text/html' and record.http_headers.get_statuscode() == "200":
        uri = record.rec_headers.get_header("uri")

        if re.search(reg, uri):
            return True
            # yield pth, date, uri  # f"http://localhost:8080/my-web-archive/{date}/{uri}"


def get_date_and_uri(record):
    uri = record.rec_headers.get_header("uri")
    date = record.rec_headers.get_header("archive-date")
    return date, uri


def retrieve_seeds(folder):
    for pth in find_arcs(folder):
        for record in iter_record(pth):
            if is_root(record):
                yield pth, get_date_and_uri(record)


if __name__ == '__main__':
    seeds = list(retrieve_seeds("2131231"))
