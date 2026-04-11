import ctypes
import time
from utils.window_session import WindowSession

# Windows API 常量
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001

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
