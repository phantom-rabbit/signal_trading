from cli import cli
from loguru import logger
import time
import pyfiglet
from colorama import Fore, Style, init

# 初始化 colorama
init(autoreset=True)

def print_startup_message():
    # 使用 pyfiglet 创建 ASCII 艺术
    title = pyfiglet.figlet_format("Signal Trading", font="slant")
    author = pyfiglet.figlet_format("Author: Phantom", font="digital")

    # 打印带颜色的启动消息
    print(Fore.CYAN + title)
    time.sleep(0.1)
    print(Fore.YELLOW + author)
    time.sleep(0.1)

    # 打印分隔线
    print(Fore.GREEN + "=" * 50)
    time.sleep(0.1)
    print(Fore.BLUE + "|               Welcome to               |")
    time.sleep(0.1)
    print(Fore.BLUE + "|           Signal Trading App           |")
    time.sleep(0.1)
    print(Fore.GREEN + "=" * 50)
    time.sleep(0.1)

if __name__ == '__main__':
    print_startup_message()
    cli()

