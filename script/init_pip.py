# -*- coding:utf-8 -*-
import os
import logging

# 目录地址配置
current_dir, _ = os.path.split(__file__)
current_dir = current_dir or os.getcwd()  # 当前目录
source_path = os.path.abspath(os.path.dirname(current_dir))  # 上一层目录，认为是源目录


def read_requirements(file_path):
    with open(file_path) as f:
        contents = f.read()
        return contents.splitlines()


def pip_requirements():
    lines = read_requirements(os.path.join(source_path, 'requirements.txt'))
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        print(line)
        print(os.popen('pip install --force-reinstall ' + line).read())
    compare(lines)


def compare(lines):
    # 生成最新列表
    print(os.popen('pip freeze > ' + os.path.join(source_path, 'requirements3.txt')).read())
    # 对比
    r3 = read_requirements(os.path.join(source_path, 'requirements3.txt'))
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line in r3:
            print('库相同', line)
        elif '==' in line:
            print('** 需要', line)
            print(os.popen('pip install --no-dependencies --force-reinstall ' + line).read())


if __name__ == "__main__":
    pip_requirements()
