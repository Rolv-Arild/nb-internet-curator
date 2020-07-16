import os
from pathlib import Path

from aiohttp import web
from aiohttp.hdrs import METH_OPTIONS
from aiohttp.web_request import Request
from aiohttp.web_routedef import options

from src.util import cd, iter_arcs, CONFIG
from pywb.manager.manager import main as wb_manager


def add_collection(*, folder):
    arc_folder = Path(CONFIG["arc_source_directory"]).absolute() / folder
    if not os.path.exists(arc_folder):
        raise ValueError

    wdir = Path(CONFIG["working_directory"]).absolute()

    do_add = True
    with cd(wdir):
        try:
            wb_manager(["init", folder])
        except FileExistsError:
            do_add = False

        if do_add:
            for arc in iter_arcs(arc_folder):
                wb_manager(["add", folder, arc])


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


if __name__ == '__main__':
    start_server()
