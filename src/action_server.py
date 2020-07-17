import os
from enum import Enum
from pathlib import Path

from aiohttp import web
from aiohttp.hdrs import METH_OPTIONS
from aiohttp.web_request import Request
from pywb.manager.manager import main as wb_manager

from src.util import cd, find_arcs, CONFIG, iter_record, is_root, get_date_and_uri, retrieve_seeds

import pandas as pd


class Verdict(Enum):
    UNDECIDED = "undecided"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class CollectionTracker:
    def __init__(self, folder, df=None):
        self.verdict_path = Path(CONFIG.result_directory).absolute() / f"{folder}.tsv"
        self.current_index = 0
        if df is None:
            self.df: pd.DataFrame = pd.read_csv(self.verdict_path)
        else:
            self.df = df
            self.save()

    def save(self):
        self.df.to_csv(self.verdict_path, sep="\t")

    def get_next(self):
        self.current_index = (self.current_index + 1) % len(self.df)
        return self.df.iloc[self.current_index]

    def get_previous(self):
        self.current_index = (self.current_index - 1) % len(self.df)
        return self.df.iloc[self.current_index]

    def get_next_undecided(self):
        row = self.get_next()
        c = 0
        while row.curator_verdict != Verdict.UNDECIDED.value and c < len(self.df):
            row = self.get_next()
            c += 1
        return row

    def get_previous_undecided(self):
        row = self.get_previous()
        c = 0
        while row.curator_verdict != Verdict.UNDECIDED.value and c < len(self.df):
            row = self.get_previous()
            c += 1
        return row

    def set_verdict(self, date, uri, verdict):
        selection = (self.df.date == date) & (self.df.uri == uri)
        self.df.loc[selection, "verdict"] = verdict
        self.save()
        if isinstance(selection, pd.Series):
            return selection.sum() > 0
        return None


def add_collection(*, folder):
    arc_folder = Path(CONFIG.arc_source_directory).absolute() / folder
    if not os.path.exists(arc_folder):
        raise ValueError

    wdir = Path(CONFIG.working_directory).absolute()

    do_add = True
    with cd(wdir):
        try:
            wb_manager(["init", folder])
        except FileExistsError:
            do_add = False

        if do_add:
            cols = ("path", "date", "uri", "curator_verdict")
            data = {c: [] for c in cols}
            for arc_path in find_arcs(arc_folder):
                wb_manager(["add", folder, arc_path])
                for record in iter_record(arc_path):
                    if is_root(record):
                        line = (arc_path, *get_date_and_uri(record), Verdict.UNDECIDED.value)
                        # print(line)
                        for c, val in zip(cols, line):
                            data[c].append(val)
    df = pd.DataFrame(data)
    collection_state[folder] = CollectionTracker(folder, df)


routes = web.RouteTableDef()


@routes.route(METH_OPTIONS, "/add_collection")
async def add_collection_options(request: Request):
    origin = request.headers.get("Origin", "")
    return web.HTTPOk(headers={"Access-Control-Allow-Origin": origin,
                               "Access-Control-Allow-Method": "POST",
                               "Access-Control-Allow-Headers": "Content-Type"})


@routes.post("/add_collection")
async def add_collection_endpoint(request: Request):
    origin = request.headers.get("Origin", "")
    data = await request.json()

    h = {"Access-Control-Allow-Origin": origin}

    try:
        add_collection(**data)
        # print(data)
        return web.HTTPOk(headers=h)
    except TypeError:
        return web.HTTPBadRequest(reason="Missing required field", headers=h)
    except ValueError:
        return web.HTTPBadRequest(reason="Folder was not in working directory", headers=h)


def start_server():
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=6969)

    return app


def init_collection_state():
    states = {}
    for folder in os.listdir(Path(CONFIG.working_directory).absolute() / "collections"):
        states[folder] = CollectionTracker(folder)
    return states


collection_state = init_collection_state()

if __name__ == '__main__':
    start_server()
