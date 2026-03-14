import sys
import threading
import time
from contextlib import contextmanager

class Logger:
    RESET = "\033[0m"
    _lock = threading.Lock()

    @staticmethod
    def _to_rgb(color: str | tuple) -> tuple[int, int, int]:
        if isinstance(color, tuple):
            return color
        color = color.strip().lstrip("#")
        if len(color) == 3:
            color = "".join(c * 2 for c in color)
        elif len(color) != 6:
            raise ValueError(f"Invalid hex color: #{color}")
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        return (r, g, b)

    @staticmethod
    def _ansi(r: int, g: int, b: int) -> str:
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def log(message: str):
        with Logger._lock:
            sys.stdout.write("\x1b[2K\r")
            print(message)

    @staticmethod
    def error(message: str):
        Logger.log_color(f"[ERROR] {message}", "#FF4C4C")

    @staticmethod
    def warning(message: str):
        Logger.log_color(f"[WARNING] {message}", "#FFA500")

    @staticmethod
    def info(message: str):
        Logger.log_color(f"[INFO] {message}", "#4CA3FF")

    @staticmethod
    def success(message: str):
        Logger.log_color(f"[SUCCESS] {message}", "#2ECC71")

    @staticmethod
    def debug(message: str):
        Logger.log_color(f"[DEBUG] {message}", "#A0A0A0")

    @staticmethod
    def log_color(message: str, color: str | tuple):
        r, g, b = Logger._to_rgb(color)
        with Logger._lock:
            sys.stdout.write("\x1b[2K\r")
            print(f"{Logger._ansi(r, g, b)}{message}{Logger.RESET}")

    @staticmethod 
    def set_text_color(text: str, color: str | tuple) -> str:
        r, g, b = Logger._to_rgb(color)
        return f"{Logger._ansi(r, g, b)}{text}{Logger.RESET}"

    @staticmethod
    def set_texts_color(text: list[str], color: list[str | tuple], space:str="") -> str:
        if len(text) != len(color):
            raise ValueError("The number of texts and colors must be equal.")

        result = ""
        for i, t in enumerate(text):
            result += Logger.set_text_color(t, color[i]) + space
        return result

    @staticmethod
    def banner():
        banner_text = r"""
      ___           ___           ___            ___           ___     
     /\  \         /\__\         /|  |          /\  \         /\__\    
     \:\  \       /:/ _/_       |:|  |          \:\  \       /:/ _/_   
      \:\  \     /:/ /\__\      |:|  |           \:\  \     /:/ /\  \  
  _____\:\  \   /:/ /:/ _/_   __|:|__|       ___  \:\  \   /:/ /::\  \ 
 /::::::::\__\ /:/_/:/ /\__\ /::::\__\_____ /\  \  \:\__\ /:/_/:/\:\__\
 \:\~~\~~\/__/ \:\/:/ /:/  / ~~~~\::::/___/ \:\  \ /:/  / \:\/:/ /:/  /
  \:\  \        \::/_/:/  /      |:|~~|      \:\  /:/  /   \::/ /:/  / 
   \:\  \        \:\/:/  /       |:|  |       \:\/:/  /     \/_/:/  /  
    \:\__\        \::/  /        |:|__|        \::/  /        /:/  /   
     \/__/         \/__/         |/__/          \/__/         \/__/                                                         
        """
        Logger.log_color(banner_text, "#4CA3FF")