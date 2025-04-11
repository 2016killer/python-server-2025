import colorama
colorama.init()
RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN
RESET = colorama.Fore.RESET

import os
import requests


current_dir = os.path.dirname(os.path.abspath(__file__))
requires = [
    os.path.join(current_dir, 'excel_db.py')
]

scripts = [
    os.path.join(current_dir, 'main.py')
]

def update_requires_2_server():
    for require_path in requires:
        response = requests.post('http://127.0.0.1:7000/file/upload/module', files={'file': open(require_path, 'rb')})
        response.raise_for_status()
        print(f'----更新依赖{GREEN}{require_path}{RESET}到服务器成功:{GREEN}{response.text}{RESET}----')

def server_scripts_parse():
    for script_path in scripts:
        server_code = ''
        in_server_block = False
        with open(scripts[0], 'r', encoding='utf-8') as file:
            for line in file:
                if '# hsc:' in line and in_server_block:
                    server_code += line.replace('# hsc:', '')
                    continue
                if '# server-code-block' in line:
                    in_server_block = not in_server_block
                    continue
                if in_server_block:
                    server_code += line

        with open(scripts[0].replace('.py', '_server.py'), 'w', encoding='utf-8') as file:
            file.write(server_code)

def run_server_codes():
    for script_path in scripts:
        script_server_path = script_path.replace('.py', '_server.py')
        with open(script_server_path, 'r', encoding='utf-8') as file:
            server_code = file.read()
        response = requests.post('http://127.0.0.1:7000/run/script', data=server_code)
        response.raise_for_status()
        print(f'----在服务器执行{GREEN}{script_server_path}{RESET}:{GREEN}{response.text}{RESET}----')
    


update_requires_2_server()
server_scripts_parse()
run_server_codes()