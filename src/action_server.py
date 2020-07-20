import os
from enum import Enum
from pathlib import Path
from typing import Callable, Union

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
        if df is None:
            self.df: pd.DataFrame = pd.read_csv(self.verdict_path, sep="\t")
        else:
            self.df = df
            self.save()

    def save(self):
        self.df.to_csv(self.verdict_path, sep="\t")

    def _get_current_index(self, date, uri):
        # print(date, uri)
        date = int(date)
        print(self.df[(self.df.date == date) & (self.df.uri == uri)])
        print(self.df.index.dtype)
        return self.df[(self.df.date == date) & (self.df.uri == uri)].index[0]

    def get_current(self, date, uri):
        return self.df.iloc[self._get_current_index(date, uri)]

    def get_next(self, date, uri):
        index = self._get_current_index(date, uri)
        index = (index + 1) % len(self.df)
        return self.df.iloc[index]

    def get_previous(self, date, uri):
        index = self._get_current_index(date, uri)
        index = (index - 1) % len(self.df)
        return self.df.iloc[index]

    def get_next_undecided(self, date, uri):
        row = self.get_next(date, uri)
        c = 0
        while row.curator_verdict != Verdict.UNDECIDED.value and c < len(self.df):
            row = self.get_next(row.date, row.uri)
            c += 1
        return row

    def get_previous_undecided(self, date, uri) -> pd.Series:
        row = self.get_previous(date, uri)
        c = 0
        while row.curator_verdict != Verdict.UNDECIDED.value and c < len(self.df):
            row = self.get_previous(row.date, row.uri)
            c += 1
        return row

    def set_verdict(self, date, uri, verdict):
        selection = (self.df.date == date) & (self.df.uri == uri)
        index = self._get_current_index(date, uri)
        verdict_index = list(self.df.columns).index("curator_verdict")
        if isinstance(verdict, Verdict):
            self.df.iloc[index, verdict_index] = verdict.value
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


@routes.route(METH_OPTIONS, "/paginate/{direction}")
async def paginate_options(request: Request):
    origin = request.headers.get("Origin", "")
    return web.HTTPOk(headers={"Access-Control-Allow-Origin": origin,
                               "Access-Control-Allow-Method": "GET",
                               "Access-Control-Allow-Headers": "Content-Type"})


@routes.get("/paginate/{direction}")
async def paginate_endpoint(request: Request):
    origin = request.headers.get("Origin", "")
    direction = request.match_info["direction"]
    query = request.query

    collection = query.get("collection", "")
    if collection == "":
        return web.HTTPBadRequest(reason="Missing required field: 'collection'")
    tracker = collection_state.get(collection, None)
    if tracker is None:
        return web.HTTPBadRequest(reason="Failed to find collection")
    date = query.get("date", "")
    if date == "":
        return web.HTTPBadRequest(reason="Missing required field: 'date'")
    url = query.get("url", "")
    if url == "":
        return web.HTTPBadRequest(reason="Missing required field: 'url'")

    method: Union[Callable[[str, str], pd.Series], None] = {
        "next": tracker.get_next,
        "previous": tracker.get_previous,
        "next_undecided": tracker.get_next_undecided,
        "previous_undecided": tracker.get_previous_undecided,
        "current": tracker.get_current
    }.get(direction, None)

    if method is None:
        return web.HTTPBadRequest(reason="Invalid direction")

    row = method(date, url)
    response = {
        "url": f"/{collection}/{str(row.date)}/{row.uri}",
        "verdict": row.curator_verdict
    }

    h = {"Access-Control-Allow-Origin": origin}
    return web.json_response(response, headers=h)


@routes.route(METH_OPTIONS, "/verdicate")
async def verdicate_options(request: Request):
    origin = request.headers.get("Origin", "")
    return web.HTTPOk(headers={"Access-Control-Allow-Origin": origin,
                               "Access-Control-Allow-Method": "POST",
                               "Access-Control-Allow-Headers": "Content-Type"})


@routes.post("/verdicate")
async def verdicate_endpoint(request: Request):
    origin = request.headers.get("Origin", "")
    data = await request.json()

    collection = data.get("collection", "")
    if collection is None:
        return web.HTTPBadRequest(reason="Missing required field: 'collection'")
    tracker = collection_state.get(collection, None)
    if tracker is None:
        return web.HTTPBadRequest(reason="Failed to find collection")
    date = data.get("date", None)
    if date is None:
        return web.HTTPBadRequest(reason="Missing required field: 'date'")
    url = data.get("url", None)
    if url is None:
        return web.HTTPBadRequest(reason="Missing required field: 'url'")
    verdict = data.get("verdict", None)
    if verdict is None:
        return web.HTTPBadRequest(reason="Missing required field: 'verdict'")

    try:
        verdict = Verdict(verdict)
    except ValueError:
        return web.HTTPBadRequest(reason="Invalid verdict")
    tracker.set_verdict(date, url, verdict)
    row = tracker.get_next_undecided(date, url)
    response = {
        "url": f"/{collection}/{str(row.date)}/{row.uri}"
    }

    h = {"Access-Control-Allow-Origin": origin}
    return web.json_response(response, headers=h)


def start_server():
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=6969)

    return app


def init_collection_state():
    states = {}

    try:
        collections = os.listdir(Path(CONFIG.working_directory).absolute() / "collections")
        for folder in collections:
            states[folder] = CollectionTracker(folder)
    except FileNotFoundError:
        pass

    return states


result_path = Path(CONFIG.result_directory).absolute()
if not os.path.exists(result_path):
    os.makedirs(result_path)

collection_state = init_collection_state()

if __name__ == '__main__':
    start_server()
