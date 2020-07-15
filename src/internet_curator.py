import os
import re

import warcio



class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def start():
    coll_name = "curator_archive"
    if not os.path.exists(coll_name):
        os.mkdir(coll_name)

    do_add = True
    with cd(coll_name):
        try:
            wb_manager(["init", coll_name])
        except FileExistsError:
            do_add = False

        while True:
            folder = input("Enter folder pls:")
            if do_add:
                for arc in iter_arcs(folder):
                    wb_manager(["add", coll_name, arc])
            wayback_cli = wayback()
            for url in search(folder):
                r = None
                while r not in "jn":
                    r = input(f"{url} godkjent (j/n)?")
                if r == "j":
                    pass
                elif r == "n":
                    pass


if __name__ == '__main__':
    start()

    # "wb-manager add my-web-archive /home/rolv-arild/Apps/PycharmProjects/soc/res/2009-01-01/491666/1/*"
