import colorama
colorama.init()
RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
BLUE = colorama.Fore.BLUE
RESET = colorama.Fore.RESET

from aiohttp import web
import time

import traceback

import logging
import os


import common



logger = logging.getLogger('python解释服务')

# --------------------APP接口--------------------
def statusColor(code):
    status = str(code) + RESET
    if code == 200: return GREEN + status
    if code // 100 == 2: return YELLOW + status
    return RED + status

def timeCostColor(timeCost):
    return BLUE + str(timeCost) + RESET



@web.middleware
async def redirection(request, handler):
    pos = f'{request.path}-{request.method.lower()}'
    logger.warning('请求路径:%s', pos)

    response = None
    try:
        common.run_timecost
        response = await handler(request)
        if response is None: 
            raise web.HTTPNotFound()
    except Exception as e:
        logger.error('%s%s%s', RED, traceback.format_exc(), RESET)
        response = web.Response(text=str(e), status=getattr(e, 'status', 500))
    finally:
        logger.warning('请求路径:%s, 响应状态码:%s, 耗时:%s', pos, statusColor(response.status))
        return response



 

app = web.Application(middlewares=[redirection])
app.add_routes([
    web.post('/product/synopsis', ...),
])
if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=7000)
    ...

