import ctypes

import win32gui


class WindowSession:
    """Shared window state for capture and background input."""

    def __init__(self, window_title):
        self.window_title = window_title
        self.hwnd = None
        self.window_rect = None

    def refresh(self):
        self.hwnd = win32gui.FindWindow(None, self.window_title)
        if not self.hwnd:
            self.window_rect = None
            return None
        self.window_rect = win32gui.GetWindowRect(self.hwnd)
        return self.hwnd

    def get_hwnd(self):
        if self.hwnd and win32gui.IsWindow(self.hwnd):
            return self.hwnd
        return self.refresh()

    def exists(self):
        return self.get_hwnd() not in (None, 0)

    def is_minimized(self):
        hwnd = self.get_hwnd()
        if not hwnd:
            return False
        return bool(win32gui.IsIconic(hwnd))

    def get_window_rect(self):
        hwnd = self.get_hwnd()
        if not hwnd:
            return None
        rect = win32gui.GetWindowRect(hwnd)
        self.window_rect = rect
        return rect

    def get_window_position(self):
        rect = self.get_window_rect()
        if rect is None:
            return None
        return (rect[0], rect[1])

    def get_window_size(self):
        rect = self.get_window_rect()
        if rect is None:
            return None
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            raise ValueError("窗口尺寸无效")
        return width, height

    def screen_to_client(self, x, y):
        hwnd = self.get_hwnd()
        if not hwnd:
            return None
        point = ctypes.wintypes.POINT(int(x), int(y))
        ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(point))
        return point.x, point.y
