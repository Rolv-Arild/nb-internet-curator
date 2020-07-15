import os
import re

import warcio
from pywb.apps.cli import wayback
from pywb.manager.manager import main as wb_manager


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def iter_arcs(folder, max_size=2 ** 33):
    for file in os.listdir(folder):
        pth = f"{folder}/{file}"
        if os.path.isdir(pth):
            for pth in iter_arcs(pth):
                max_size -= os.path.getsize(pth)
                if max_size < 0:
                    return
                yield pth
            # yield from iter_arcs(pth, max_size)
        elif os.path.isfile(pth) and "arc" in file:
            max_size -= os.path.getsize(pth)
            if max_size < 0:
                return
            yield pth


def iter_records(folder):
    for pth in iter_arcs(folder):
        with open(pth, "rb") as stream:
            for record in warcio.archiveiterator.ARCIterator(stream):
                yield record


def search(folder, s=None):
    if s is None:
        s = "^https?:\/\/[\w.]+no(:\d+)?\/?$"
    for record in iter_records(folder):
        if record.content_type == 'text/html' and record.http_headers.get_statuscode() == "200":
            uri = record.rec_headers.get_header("uri")
            date = record.rec_headers.get_header("archive-date")
            if re.search(s, uri):
                yield f"http://localhost:8080/my-web-archive/{date}/{uri}"
