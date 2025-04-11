import importlib
import aiofile
import colorama
colorama.init()
RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
BLUE = colorama.Fore.BLUE
RESET = colorama.Fore.RESET

from aiohttp import web
import traceback

import logging
import os
import sys
logger = logging.getLogger('python解释服务')
current_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.join(current_dir, 'modules')

def init():
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(stream_handler)

    for file in list(os.listdir(module_dir)):
        module_name = None

        if file.endswith('.py'):
            if file == '__init__.py': continue
            module_name = file[:-3]
        elif os.path.isdir(os.path.join(module_dir, file)):
            subdir_path = os.path.join(module_dir, file)
            if '__init__.py' in os.listdir(subdir_path): module_name = file
        
        if module_name:
            try:
                load_module(module_name)
            except Exception as e: 
                logger.error(f'{RED}导入模块:{module_name}, 错误:{e}{RESET}\n{traceback.format_exc()}')


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
        response = await handler(request)
        if response is None: raise web.HTTPNotFound()
    except Exception as e:
        logger.error('%s%s%s', RED, traceback.format_exc(), RESET)
        response = web.Response(text=str(e), status=getattr(e, 'status', getattr(e,'status_code',500)))
    finally:
        logger.warning('请求路径:%s, 响应状态码:%s', pos, statusColor(response.status))
        return response

def load_module(module_name):
    '''加载模块'''
    module_name = f'modules.{module_name}'
    logger.warning(f'{YELLOW}导入模块:{module_name}{RESET}')
    importlib.import_module(module_name)


async def upload_module_api(request):
    '''上传脚本'''
    # 加载参数
    data = await request.post()
    file, hot_start = data['file'], data.get('hot_start', False)
    filename = file.filename

    # 保存文件
    async with aiofile.AIOFile(os.path.join(module_dir, filename), 'wb') as afp:
        writer = aiofile.Writer(afp)
        file_content = file.file.read()
        await writer(file_content)
        await afp.fsync()

    # 热启动
    if hot_start: load_module(filename[:-3])

    return web.Response(text='上传成功')

async def load_module_api(request):
    '''加载脚本'''
    data = await request.json()
    load_module(data['module'])
    return web.Response(text='加载成功')

async def run_script_api(request):
    '''运行脚本'''
    script = await request.text()
    local_namespace = dict()
    exec(script, globals(), local_namespace)
    return web.Response(text=local_namespace.get('resinfo', '运行成功'))

app = web.Application(middlewares=[redirection])
app.add_routes([
    web.post('/file/upload/module', upload_module_api),
    web.post('/load/module', load_module_api),
    web.post('/run/script', run_script_api),
])


if __name__ == '__main__':
    init()
    web.run_app(app, host='127.0.0.1', port=7000)
    ...

