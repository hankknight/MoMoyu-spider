import os
import functools


def folder(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        current_folder = os.path.dirname(__file__)
        img_folder = os.path.join(os.path.dirname(current_folder), "img")
        if not os.path.exists(img_folder):
            os.mkdir(img_folder)
        func(*args, **kwargs)

    return wrapper
