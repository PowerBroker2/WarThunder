import os
import sys


def get_version(game_path: str = None) -> str:
    if game_path is None:
        if sys.platform == 'win32':
            game_path = r'C:\Program Files (x86)\Steam\steamapps\common\War Thunder'
        elif sys.platform == 'darwin':
            game_path = os.path.expanduser('~/Library/Application Support/Steam/steamapps/common/War Thunder')
        else:
            game_path = os.path.expanduser('~/.local/share/Steam/steamapps/common/War Thunder')

    try:
        with open(os.path.join(game_path, 'content', 'pkg_main.ver')) as file:
            return file.read().strip()
    except FileNotFoundError:
        return '1.0.0'