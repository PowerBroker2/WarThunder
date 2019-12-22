import os


def get_version(game_path=r'C:\Program Files (x86)\Steam\steamapps\common\War Thunder'):
    with open(os.path.join(game_path, r'content\pkg_main.ver')) as file:
        return file.read()