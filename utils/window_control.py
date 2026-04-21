import ctypes
import time
import win32gui
from utils.window_session import WindowSession

# Windows API 常量
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001
SW_HIDE = 0
SW_SHOW = 5
HIDDEN_OFFSET_X = 50000
HIDDEN_OFFSET_Y = 50000
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020

class WindowControl:
    """Windows 窗口后台控制类，支持后台静默点击"""
    
    def __init__(self, window_title, window_session=None):
        """
        初始化窗口控制器
        
        Args:
            window_title: 窗口标题
        """
        self.window_title = window_title
        self.window_session = window_session or WindowSession(window_title)
        self.hwnd = None
        self._restored_rect = None
        self._original_exstyle = None

    def _set_taskbar_visible(self, visible):
        """切换任务栏可见性，不改变窗口句柄。"""
        if not self.find_window():
            return False

        exstyle = ctypes.windll.user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        if self._original_exstyle is None:
            self._original_exstyle = exstyle

        if visible:
            new_exstyle = self._original_exstyle
        else:
            new_exstyle = (exstyle | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW

        if new_exstyle != exstyle:
            ctypes.windll.user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, new_exstyle)
            ctypes.windll.user32.SetWindowPos(
                self.hwnd,
                0,
                0,
                0,
                0,
                0,
                SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
            )
        return True
    
    def find_window(self):
        """
        查找窗口句柄
        
        Returns:
            bool: 是否找到窗口
        """
        try:
            self.hwnd = self.window_session.get_hwnd()
            if self.hwnd:
                return True
            else:
                return False
        except Exception as e:
            print(f"查找窗口失败：{e}")
            return False
    
    def is_window_visible(self):
        """检查窗口是否可见"""
        hwnd = self.window_session.get_hwnd()
        if not hwnd:
            return False
        self.hwnd = hwnd
        return ctypes.windll.user32.IsWindowVisible(hwnd)
    
    def get_window_rect(self):
        """
        获取窗口位置
        
        Returns:
            tuple: (left, top, right, bottom) 或 None
        """
        return self.window_session.get_window_rect()
    
    def click(self, x, y, duration=0.1):
        """
        在窗口内指定坐标执行后台点击（相对于窗口左上角）
        
        Args:
            x: 相对于窗口客户区的 x 坐标
            y: 相对于窗口客户区的 y 坐标
            duration: 点击持续时间（秒）
        
        Returns:
            bool: 是否点击成功
        """
        if not self.find_window():
            print("未找到窗口")
            return False
        
        # 将屏幕坐标转换为窗口客户区坐标
        client_coord = self.window_session.screen_to_client(x, y)
        if client_coord is None:
            return False
        client_x, client_y = client_coord
        
        # 构造 LPARAM 参数 (x, y)
        lparam = (client_y << 16) | (client_x & 0xFFFF)
        
        # 发送鼠标按下消息
        ctypes.windll.user32.PostMessageW(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        time.sleep(duration / 2)
        
        # 发送鼠标释放消息
        ctypes.windll.user32.PostMessageW(self.hwnd, WM_LBUTTONUP, 0, lparam)
        
        return True
    
    def double_click(self, x, y, duration=0.1):
        """
        在窗口内指定坐标执行后台双击
        
        Args:
            x: 相对于窗口客户区的 x 坐标
            y: 相对于窗口客户区的 y 坐标
            duration: 每次点击的持续时间（秒）
        """
        self.click(x, y, duration)
        time.sleep(0.1)
        self.click(x, y, duration)

    def hide_window(self):
        """把窗口移出可视区域，但保留句柄以便继续后台截图和点击。"""
        if not self.find_window():
            return False

        rect = self.window_session.get_window_rect()
        if rect is None:
            return False

        self._restored_rect = rect
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            return False

        self._set_taskbar_visible(False)
        ctypes.windll.user32.ShowWindow(self.hwnd, SW_SHOW)
        return bool(win32gui.MoveWindow(self.hwnd, HIDDEN_OFFSET_X, HIDDEN_OFFSET_Y, width, height, True))

    def show_window(self):
        """把窗口恢复到原来的位置。"""
        if not self.find_window():
            return False

        self._set_taskbar_visible(True)

        if self._restored_rect is not None:
            left, top, right, bottom = self._restored_rect
            width = right - left
            height = bottom - top
            if width > 0 and height > 0:
                result = win32gui.MoveWindow(self.hwnd, left, top, width, height, True)
                ctypes.windll.user32.ShowWindow(self.hwnd, SW_SHOW)
                return bool(result)

        return bool(ctypes.windll.user32.ShowWindow(self.hwnd, SW_SHOW))

    def set_window_hidden(self, hidden):
        """根据开关切换窗口可见性。"""
        if hidden:
            return self.hide_window()
        return self.show_window()
