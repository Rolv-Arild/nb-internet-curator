from pathlib import Path

from src.action_server import start_server
from multiprocessing import Process

import os
import shutil

from pywb.apps.cli import wayback
from pywb.manager.manager import main as wb_manager

from src.util import cd, CONFIG


def move(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)  # TODO don't nuke
    shutil.copytree(src, dst)


def init_wayback(working_dir):
    res = Path(__file__).parent.absolute() / "res"
    work_dir = Path(working_dir).absolute()
    templates_src = res / "templates"
    templates_dst = work_dir / "templates"
    static_src = res / "static"
    static_dst = work_dir / "static"

    move(templates_src, templates_dst)
    move(static_src, static_dst)

    with cd(working_dir):
        wayback()


if __name__ == '__main__':
    wdir = CONFIG.working_directory
    wP = Process(target=init_wayback, args=(wdir,))
    sP = Process(target=start_server)

    wP.start()
    sP.start()

    wP.join()
    sP.join()
