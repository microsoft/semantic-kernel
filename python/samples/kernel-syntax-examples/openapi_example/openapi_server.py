from aiohttp import web



"""Server"""
routes = web.RouteTableDef()

@routes.post('/{name}')
async def hello(request):
    # Get path parameters
    name = request.match_info.get('name', "")
    # Get query parameters
    q = request.rel_url.query.get('q', "")
    # Get body
    body = await request.json()
    # Get headers
    headers = request.headers
    return web.Response(text=f"Hello, {name}: q={q}, body={body}, headers={headers}")

app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    web.run_app(app)
