import os

from aiohttp import web
from aiohttp.web_request import Request

from src.util import cd, iter_arcs, wb_manager


def add_collection(*, name, folder):
    if not os.path.exists(name):
        os.mkdir(name)

    do_add = True
    with cd(name):
        try:
            wb_manager(["init", name])
        except FileExistsError:
            do_add = False

        if do_add:
            for arc in iter_arcs(folder):
                wb_manager(["add", name, arc])


routes = web.RouteTableDef()

@routes.post("/add_collection")
async def add_collection_endpoint(request: Request):
    data = await request.json()

    try:
        add_collection(**data)
        return web.HTTPOk()
    except TypeError:
        return web.HTTPBadRequest(reason="Missing required field")

def start_server():
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=6969)

    return app


if __name__ == '__main__':
    start_server()
