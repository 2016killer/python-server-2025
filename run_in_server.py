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


def run_scripts_in_server():
    for script in scripts:
        code = ''
        with open(script, 'r', encoding='utf-8') as file:
            next(file)  
            for line in file: code += line

        response = requests.post('http://127.0.0.1:7000/run/script', data=code)
        response.raise_for_status()
        print(f'----在服务器执行{GREEN}{script}{RESET}:{GREEN}{response.text}{RESET}----')
    

update_requires_2_server()
run_scripts_in_server()