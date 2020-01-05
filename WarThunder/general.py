import os


def get_version(game_path=r'C:\Program Files (x86)\Steam\steamapps\common\War Thunder'):
    try:
        with open(os.path.join(game_path, r'content\pkg_main.ver')) as file:
            return file.read()
    except FileNotFoundError:
        return '1.0.0'
