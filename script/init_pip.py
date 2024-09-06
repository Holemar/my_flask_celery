# -*- coding:utf-8 -*-
"""
强行导入 requirement 文件
"""
import os

from __init__ import CURRENT_DIR, SOURCE_PATH  # 导入环境


def read_requirements(file_path):
    with open(file_path, encoding='utf-8') as f:
        contents = f.read()
        lines = contents.splitlines()
        lines = [l.lower().replace('_', '-') for l in lines]
        return lines


def pip_requirements():
    lines = read_requirements(os.path.join(SOURCE_PATH, 'requirements.txt'))
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        print(line)
        print(os.popen('pip install --force-reinstall ' + line, ).read())
    compare(lines)


def compare(lines):
    # 生成最新列表
    bak_file = os.path.join(SOURCE_PATH, 'requirements_bak.txt')
    print(os.popen('pip freeze > ' + bak_file).read())
    # 对比
    r3 = read_requirements(bak_file)
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
