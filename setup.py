# type: ignore
from os import getcwd
from os.path import (
    join,
    exists,
    isfile
)

from setuptools import setup, find_namespace_packages

from ext_kit_shop import __appname__
from versioneer import get_cmdclass, get_version


def install_requires(file: str = 'requirements.txt'):
    """
    Получение списка зависимостей из файла requirements.txt (должен располагаться в корне проекта)
    """
    ret_val = []

    file_path = join(getcwd(), file)

    # Проверка на существование файла
    if not exists(file_path) or not isfile(file_path):
        return ret_val

    with open(file_path) as f:
        for line in f:
            # Удаляем комментарии
            line = line.split('#', 1)[0].strip()

            # И аргументы pip
            line = line.split('--', 1)[0].strip()

            if line:
                ret_val.append(line)

    return ret_val

setup(
    name=__appname__,
    version=get_version(),
    cmdclass=get_cmdclass(),
    packages=find_namespace_packages(include=['ext_kit_shop.*']),
    include_package_data=True,
    author='ilya Barinov',
    author_email='<i-barinov@it-serv.ru>',
    url='https://github.com/Colobok2002/ExtRtKey',
    install_requires=install_requires(),
)
