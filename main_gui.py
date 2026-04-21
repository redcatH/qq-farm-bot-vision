import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import logging
import configparser
import time
from utils.farm_bot_cv import FarmBotCV


class LogHandler(logging.Handler):
    """自定义日志处理器，将日志发送到GUI"""
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)


class ThresholdConfigDialog:
    """阈值配置对话框"""
    
    def __init__(self, parent, config_path):
        self.parent = parent
        self.config_path = config_path
        self.config = configparser.ConfigParser(inline_comment_prefixes=('#',))
        self.config.read(config_path, encoding="utf-8")
        
        # 创建顶层窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("阈值配置")
        self.dialog.geometry("700x650")
        self.dialog.resizable(True, True)
        
        # 居中显示
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建界面
        self.create_widgets()
        
        # 加载当前配置
        self.load_config()
    
    def create_widgets(self):
        """创建阈值配置界面"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="视觉匹配阈值配置", 
                               font=("Microsoft YaHei", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        # 创建滚动框架
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 鼠标滚轮支持
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # 阈值配置项分组
        self.threshold_vars = {}
        
        # 好友列表相关阈值
        friend_frame = ttk.LabelFrame(scrollable_frame, text="好友列表相关阈值", padding="10")
        friend_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.create_threshold_input(friend_frame, "help_remove_bugs_frame", "好友有虫图标", 0)
        self.create_threshold_input(friend_frame, "help_remove_grass_frame", "好友有草图标", 1)
        self.create_threshold_input(friend_frame, "help_watering_frame", "好友干土地图标", 2)
        self.create_threshold_input(friend_frame, "can_steal_frame", "好友可偷取图标", 3)
        
        # 按钮和界面相关阈值
        button_frame = ttk.LabelFrame(scrollable_frame, text="按钮和界面阈值", padding="10")
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.create_threshold_input(button_frame, "close_x_frame", "关闭按钮X", 0)
        self.create_threshold_input(button_frame, "go_home_frame", "回家按钮", 1)
        self.create_threshold_input(button_frame, "return_farm_frame", "返回农场按钮", 2)
        self.create_threshold_input(button_frame, "friend_icon_frame", "好友图标", 3)
        
        # 操作功能阈值
        action_frame = ttk.LabelFrame(scrollable_frame, text="操作功能阈值", padding="10")
        action_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.create_threshold_input(action_frame, "steal_all_frame", "一键偷取", 0)
        self.create_threshold_input(action_frame, "watering_all_frame", "一键浇水", 1)
        self.create_threshold_input(action_frame, "remove_all_grass_frame", "一键除草", 2)
        self.create_threshold_input(action_frame, "remove_all_bugs_frame", "一键除虫", 3)
        self.create_threshold_input(action_frame, "harvest_all_frame", "一键收获", 4)
        self.create_threshold_input(action_frame, "harvest_one_frame", "单个收获", 5)
        
        # 弹窗和小图标阈值
        popup_frame = ttk.LabelFrame(scrollable_frame, text="弹窗和小图标阈值", padding="10")
        popup_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.create_threshold_input(popup_frame, "can_steal_small_frame", "小弹窗-可偷标志", 0)
        self.create_threshold_input(popup_frame, "can_watering_small_frame", "小弹窗-可浇水标志", 1)
        self.create_threshold_input(popup_frame, "can_remove_grass_small_frame", "小弹窗-可除草标志", 2)
        self.create_threshold_input(popup_frame, "can_remove_bugs_small_frame", "小弹窗-可除虫标志", 3)
        self.create_threshold_input(popup_frame, "close_x_small_frame", "小弹窗-关闭按钮", 4)
        
        # 其他界面阈值
        other_frame = ttk.LabelFrame(scrollable_frame, text="其他界面阈值", padding="10")
        other_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.create_threshold_input(other_frame, "welcome_back_frame", "欢迎回来界面", 0)
        self.create_threshold_input(other_frame, "get_new_seed_frame", "获得新种子界面", 1)
        self.create_threshold_input(other_frame, "level_up_frame", "升级界面", 2)
        self.create_threshold_input(other_frame, "reconnect_frame", "重连按钮", 3)
        self.create_threshold_input(other_frame, "shop_red_frame", "红点商店图标", 4)
        self.create_threshold_input(other_frame, "daily_free_frame", "每日免费礼包", 5)
        self.create_threshold_input(other_frame, "dog_house_frame", "狗窝图标", 6)
        self.create_threshold_input(other_frame, "remove_seed_frame", "移除种子图标", 7)
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, pady=(10, 0), sticky=tk.E)
        
        save_btn = ttk.Button(btn_frame, text="保存配置", command=self.save_config)
        save_btn.grid(row=0, column=0, padx=5)
        
        cancel_btn = ttk.Button(btn_frame, text="取消", command=self.dialog.destroy)
        cancel_btn.grid(row=0, column=1, padx=5)
        
        reset_btn = ttk.Button(btn_frame, text="恢复默认", command=self.reset_to_default)
        reset_btn.grid(row=0, column=2, padx=5)
    
    def create_threshold_input(self, parent, key, label, row):
        """创建阈值输入框"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
        frame.columnconfigure(1, weight=1)
        
        label_widget = ttk.Label(frame, text=f"{label}:", width=20)
        label_widget.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        var = tk.StringVar()
        self.threshold_vars[key] = var
        
        entry = ttk.Entry(frame, textvariable=var, width=15)
        entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        unit_label = ttk.Label(frame, text="(0.0-1.0)")
        unit_label.grid(row=0, column=2, sticky=tk.W)
    
    def load_config(self):
        """加载当前配置"""
        for key, var in self.threshold_vars.items():
            try:
                value = self.config.get('threshold', key)
                var.set(value)
            except:
                var.set("0.5")  # 默认值
    
    def save_config(self):
        """保存配置"""
        try:
            # 验证并保存所有阈值
            for key, var in self.threshold_vars.items():
                value = var.get().strip()
                
                # 验证是否为有效数字
                try:
                    float_value = float(value)
                    if float_value < 0 or float_value > 1:
                        messagebox.showerror("错误", f"阈值 {key} 的值必须在 0.0 到 1.0 之间")
                        return
                except ValueError:
                    messagebox.showerror("错误", f"阈值 {key} 的值必须是数字")
                    return
                
                # 更新配置
                self.config.set('threshold', key, value)
            
            # 写入文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            messagebox.showinfo("成功", "阈值配置已保存！")
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{str(e)}")
    
    def reset_to_default(self):
        """恢复默认值"""
        defaults = {
            'help_remove_bugs_frame': '0.6',
            'help_remove_grass_frame': '0.6',
            'help_watering_frame': '0.6',
            'can_steal_frame': '0.6',
            'close_x_frame': '0.6',
            'go_home_frame': '0.5',
            'steal_all_frame': '0.5',
            'watering_all_frame': '0.4',
            'remove_all_grass_frame': '0.4',
            'remove_all_bugs_frame': '0.5',
            'harvest_all_frame': '0.4',
            'harvest_one_frame': '0.4',
            'friend_icon_frame': '0.47',
            'welcome_back_frame': '0.65',
            'get_new_seed_frame': '0.4',
            'level_up_frame': '0.6',
            'reconnect_frame': '0.5',
            'can_steal_small_frame': '0.6',
            'can_watering_small_frame': '0.6',
            'can_remove_grass_small_frame': '0.6',
            'can_remove_bugs_small_frame': '0.6',
            'close_x_small_frame': '0.6',
            'shop_red_frame': '0.4',
            'daily_free_frame': '0.4',
            'return_farm_frame': '0.6',
            'dog_house_frame': '0.6',
            'remove_seed_frame': '0.6'
        }
        
        for key, default_value in defaults.items():
            if key in self.threshold_vars:
                self.threshold_vars[key].set(default_value)


class FarmBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("QQ农场机器人视觉版 - 可视化控制面板")
        self.root.geometry("950x900")
        
        # 日志队列
        self.log_queue = queue.Queue()
        
        # 机器人实例
        self.bot = None
        self.bot_thread = None
        self.is_running = False
        self.is_paused = False
        
        # 加载配置
        self.config_path = "config.ini"
        self.config = configparser.ConfigParser(inline_comment_prefixes=('#',))
        self.config.read(self.config_path, encoding="utf-8")
        
        # 创建界面
        self.create_widgets()
        
        # 启动日志更新线程
        self.update_log()
        
        # 启动状态同步线程（监听热键变化）
        self.start_status_sync()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """创建GUI组件"""
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # ===== 标题 =====
        title_label = ttk.Label(main_frame, text="QQ农场机器人视觉版控制面板", 
                               font=("Microsoft YaHei", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        # ===== 控制按钮区域 =====
        control_frame = ttk.LabelFrame(main_frame, text="机器人控制", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=0, column=0, sticky=tk.W)
        
        # 启动按钮
        self.start_btn = ttk.Button(btn_frame, text="启动机器人", 
                                    command=self.start_bot, width=15)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        # 暂停/恢复按钮
        self.pause_btn = ttk.Button(btn_frame, text="暂停", 
                                   command=self.toggle_pause, width=15, state=tk.DISABLED)
        self.pause_btn.grid(row=0, column=1, padx=5)
        
        # 停止按钮
        self.stop_btn = ttk.Button(btn_frame, text="停止", 
                                  command=self.stop_bot, width=15, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=5)
        
        # 阈值配置按钮
        self.threshold_btn = ttk.Button(btn_frame, text="阈值配置", 
                                       command=self.open_threshold_config, width=15)
        self.threshold_btn.grid(row=0, column=3, padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="状态: 未运行")
        status_label = ttk.Label(btn_frame, textvariable=self.status_var, 
                                font=("Microsoft YaHei", 10))
        status_label.grid(row=0, column=4, padx=20)
        
        # ===== 间隔时长配置区域 =====
        interval_frame = ttk.LabelFrame(main_frame, text="间隔时长配置（秒）", padding="10")
        interval_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        interval_frame.columnconfigure(0, weight=1)
        interval_frame.columnconfigure(1, weight=1)
        interval_frame.columnconfigure(2, weight=1)
        
        # 机器人轮询间隔
        interval_col1 = ttk.Frame(interval_frame)
        interval_col1.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(interval_col1, text="机器人轮询间隔:", 
                 font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.check_interval_var = tk.StringVar(
            value=self.config.get('bot', 'check_interval'))
        self.check_interval_entry = ttk.Entry(interval_col1, textvariable=self.check_interval_var, width=15)
        self.check_interval_entry.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(interval_col1, text="(单位: 秒)", 
                 font=("Microsoft YaHei", 8), foreground="gray").grid(row=2, column=0, sticky=tk.W)
        
        # 检查好友农场间隔
        interval_col2 = ttk.Frame(interval_frame)
        interval_col2.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(interval_col2, text="检查好友农场间隔:", 
                 font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.friend_colddown_time_var = tk.StringVar(
            value=self.config.get('bot', 'friend_colddown_time'))
        self.friend_colddown_time_entry = ttk.Entry(interval_col2, textvariable=self.friend_colddown_time_var, width=15)
        self.friend_colddown_time_entry.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(interval_col2, text="(单位: 秒)", 
                 font=("Microsoft YaHei", 8), foreground="gray").grid(row=2, column=0, sticky=tk.W)
        
        # 种子种植状态检查间隔
        interval_col3 = ttk.Frame(interval_frame)
        interval_col3.grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(interval_col3, text="种子种植检查间隔:", 
                 font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.plant_seed_check_interval_var = tk.StringVar(
            value=self.config.get('self', 'plant_seed_check_interval'))
        self.plant_seed_check_interval_entry = ttk.Entry(interval_col3, textvariable=self.plant_seed_check_interval_var, width=15)
        self.plant_seed_check_interval_entry.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(interval_col3, text="(单位: 秒)", 
                 font=("Microsoft YaHei", 8), foreground="gray").grid(row=2, column=0, sticky=tk.W)
        
        # 应用按钮
        apply_btn = ttk.Button(interval_frame, text="应用配置", command=self.apply_interval_config)
        apply_btn.grid(row=0, column=3, padx=20, sticky=tk.E)
        
        # ===== 全局配置区域 =====
        global_config_frame = ttk.LabelFrame(main_frame, text="全局配置", padding="10")
        global_config_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        global_config_frame.columnconfigure(0, weight=1)
        global_config_frame.columnconfigure(1, weight=1)
        global_config_frame.columnconfigure(2, weight=1)
        
        # 第一列
        col1_frame = ttk.Frame(global_config_frame)
        col1_frame.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        self.enable_process_self_var = tk.BooleanVar(
            value=self.config.getboolean('bot', 'enable_process_self'))
        self.enable_process_self_cb = ttk.Checkbutton(
            col1_frame, text="启用自家农场处理", variable=self.enable_process_self_var,
            command=self.on_config_change)
        self.enable_process_self_cb.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.enable_daily_free_var = tk.BooleanVar(
            value=self.config.getboolean('self', 'enable_daily_free'))
        self.enable_daily_free_cb = ttk.Checkbutton(
            col1_frame, text="领取每日礼包", variable=self.enable_daily_free_var,
            command=self.on_config_change)
        self.enable_daily_free_cb.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 第二列
        col2_frame = ttk.Frame(global_config_frame)
        col2_frame.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.enable_process_friend_var = tk.BooleanVar(
            value=self.config.getboolean('bot', 'enable_process_friend'))
        self.enable_process_friend_cb = ttk.Checkbutton(
            col2_frame, text="启用好友农场处理", variable=self.enable_process_friend_var,
            command=self.on_config_change)
        self.enable_process_friend_cb.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.enable_plant_seed_var = tk.BooleanVar(
            value=self.config.getboolean('self', 'enable_plant_seed'))
        self.enable_plant_seed_cb = ttk.Checkbutton(
            col2_frame, text="自动种植", variable=self.enable_plant_seed_var,
            command=self.on_config_change)
        self.enable_plant_seed_cb.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 第三列
        col3_frame = ttk.Frame(global_config_frame)
        col3_frame.grid(row=0, column=2, sticky=tk.W)
        
        self.enable_silence_click_var = tk.BooleanVar(
            value=self.config.getboolean('bot', 'enable_silence_click'))
        self.enable_silence_click_cb = ttk.Checkbutton(
            col3_frame, text="后台静默点击", variable=self.enable_silence_click_var,
            command=self.on_config_change)
        self.enable_silence_click_cb.grid(row=0, column=0, sticky=tk.W, pady=2)

        self.enable_hide_window_var = tk.BooleanVar(
            value=self.config.getboolean('bot', 'enable_hide_window', fallback=False))
        self.enable_hide_window_cb = ttk.Checkbutton(
            col3_frame, text="隐藏窗口（需后台点击）", variable=self.enable_hide_window_var,
            command=self.on_config_change)
        self.enable_hide_window_cb.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # ===== 功能开关区域 =====
        settings_frame = ttk.LabelFrame(main_frame, text="功能配置", padding="10")
        settings_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        
        # 左侧：自家农场功能
        left_frame = ttk.Frame(settings_frame)
        left_frame.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(left_frame, text="自家农场功能", 
                 font=("Microsoft YaHei", 11, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 收获功能
        self.enable_harvest_var = tk.BooleanVar(
            value=self.config.getboolean('self', 'enable_harvest'))
        self.enable_harvest_cb = ttk.Checkbutton(
            left_frame, text="自动收获", variable=self.enable_harvest_var,
            command=self.on_config_change)
        self.enable_harvest_cb.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 浇水功能
        self.enable_watering_var = tk.BooleanVar(
            value=self.config.getboolean('self', 'enable_watering'))
        self.enable_watering_cb = ttk.Checkbutton(
            left_frame, text="自动浇水", variable=self.enable_watering_var,
            command=self.on_config_change)
        self.enable_watering_cb.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # 除草功能
        self.enable_remove_grass_var = tk.BooleanVar(
            value=self.config.getboolean('self', 'enable_remove_grass'))
        self.enable_remove_grass_cb = ttk.Checkbutton(
            left_frame, text="自动除草", variable=self.enable_remove_grass_var,
            command=self.on_config_change)
        self.enable_remove_grass_cb.grid(row=3, column=0, sticky=tk.W, pady=2)
        
        # 除虫功能
        self.enable_remove_bug_var = tk.BooleanVar(
            value=self.config.getboolean('self', 'enable_remove_bug'))
        self.enable_remove_bug_cb = ttk.Checkbutton(
            left_frame, text="自动除虫", variable=self.enable_remove_bug_var,
            command=self.on_config_change)
        self.enable_remove_bug_cb.grid(row=4, column=0, sticky=tk.W, pady=2)
        
        # 右侧：好友农场功能
        right_frame = ttk.Frame(settings_frame)
        right_frame.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(right_frame, text="好友农场功能", 
                 font=("Microsoft YaHei", 11, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 偷菜功能
        self.enable_steal_var = tk.BooleanVar(
            value=self.config.getboolean('friend', 'enable_steal'))
        self.enable_steal_cb = ttk.Checkbutton(
            right_frame, text="自动偷菜", variable=self.enable_steal_var,
            command=self.on_config_change)
        self.enable_steal_cb.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 帮忙浇水
        self.enable_help_watering_var = tk.BooleanVar(
            value=self.config.getboolean('friend', 'enable_help_watering'))
        self.enable_help_watering_cb = ttk.Checkbutton(
            right_frame, text="帮忙浇水", variable=self.enable_help_watering_var,
            command=self.on_config_change)
        self.enable_help_watering_cb.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # 帮忙除草
        self.enable_help_remove_grass_var = tk.BooleanVar(
            value=self.config.getboolean('friend', 'enable_help_remove_grass'))
        self.enable_help_remove_grass_cb = ttk.Checkbutton(
            right_frame, text="帮忙除草", variable=self.enable_help_remove_grass_var,
            command=self.on_config_change)
        self.enable_help_remove_grass_cb.grid(row=3, column=0, sticky=tk.W, pady=2)
        
        # 帮忙除虫
        self.enable_help_remove_bugs_var = tk.BooleanVar(
            value=self.config.getboolean('friend', 'enable_help_remove_bugs'))
        self.enable_help_remove_bugs_cb = ttk.Checkbutton(
            right_frame, text="帮忙除虫", variable=self.enable_help_remove_bugs_var,
            command=self.on_config_change)
        self.enable_help_remove_bugs_cb.grid(row=4, column=0, sticky=tk.W, pady=2)
        
        # ===== 日志显示区域 =====
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 创建滚动文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80,
                                                  wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置日志颜色标签
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("DEBUG", foreground="gray")
        
        # 清空日志按钮
        clear_btn = ttk.Button(log_frame, text="清空日志", command=self.clear_log)
        clear_btn.grid(row=1, column=0, pady=(5, 0), sticky=tk.E)
        
        # ===== 底部信息 =====
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=6, column=0, sticky=tk.W)
        
        info_label = ttk.Label(info_frame, 
                              text="提示: 保留原有热键功能 (Ctrl+C停止, P暂停/恢复)",
                              font=("Microsoft YaHei", 9), foreground="blue")
        info_label.pack(anchor=tk.W)
    
    def start_status_sync(self):
        """启动状态同步线程，监听机器人状态变化"""
        def sync_loop():
            while True:
                if self.bot and self.is_running:
                    # 检查机器人的实际暂停状态
                    actual_paused = self.bot.pause_status
                    
                    # 如果状态不一致，同步更新UI
                    if actual_paused != self.is_paused:
                        self.is_paused = actual_paused
                        # 使用after方法在主线程中更新UI
                        self.root.after(0, self.sync_ui_state)
                
                time.sleep(0.5)  # 每0.5秒检查一次
        
        sync_thread = threading.Thread(target=sync_loop, daemon=True)
        sync_thread.start()
    
    def sync_ui_state(self):
        """同步UI状态到当前机器人状态"""
        if self.is_paused:
            self.pause_btn.config(text="恢复")
            self.status_var.set("状态: 已暂停")
        else:
            self.pause_btn.config(text="暂停")
            self.status_var.set("状态: 运行中")
    
    def update_log(self):
        """定期从队列中获取日志并更新到文本框"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, msg + "\n")
                
                # 根据日志级别设置颜色
                if "ERROR" in msg:
                    self.log_text.tag_add("ERROR", "end-2l linestart", "end-2l lineend")
                elif "WARNING" in msg:
                    self.log_text.tag_add("WARNING", "end-2l linestart", "end-2l lineend")
                elif "DEBUG" in msg:
                    self.log_text.tag_add("DEBUG", "end-2l linestart", "end-2l lineend")
                else:
                    self.log_text.tag_add("INFO", "end-2l linestart", "end-2l lineend")
                
                self.log_text.see(tk.END)  # 自动滚动到底部
        except queue.Empty:
            pass
        
        # 每100ms检查一次
        self.root.after(100, self.update_log)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def setup_logging(self):
        """设置日志系统"""
        # 创建自定义日志处理器
        log_handler = LogHandler(self.log_queue)
        log_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(formatter)
        
        # 添加到根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(log_handler)
    
    def open_threshold_config(self):
        """打开阈值配置对话框"""
        # 检查是否在运行且未暂停
        if self.is_running and not self.is_paused:
            messagebox.showwarning("警告", "请先暂停或停止机器人后再配置阈值！")
            return
        
        # 打开阈值配置对话框
        ThresholdConfigDialog(self.root, self.config_path)
    
    def apply_interval_config(self):
        """应用间隔时长配置"""
        # 检查是否在运行且未暂停
        if self.is_running and not self.is_paused:
            messagebox.showwarning("警告", "请先暂停或停止机器人后再配置间隔时长！")
            return
        
        try:
            # 验证并获取配置值
            check_interval = float(self.check_interval_var.get().strip())
            friend_colddown_time = int(self.friend_colddown_time_var.get().strip())
            plant_seed_check_interval = int(self.plant_seed_check_interval_var.get().strip())
            
            # 验证范围
            if check_interval <= 0:
                messagebox.showerror("错误", "机器人轮询间隔必须大于0")
                return
            if friend_colddown_time < 0:
                messagebox.showerror("错误", "检查好友农场间隔不能为负数")
                return
            if plant_seed_check_interval < 0:
                messagebox.showerror("错误", "种子种植检查间隔不能为负数")
                return
            
            # 保存到配置文件
            self.config.set('bot', 'check_interval', str(check_interval))
            self.config.set('bot', 'friend_colddown_time', str(friend_colddown_time))
            self.config.set('self', 'plant_seed_check_interval', str(plant_seed_check_interval))
            self.config.set('bot', 'enable_hide_window', str(self.enable_hide_window_var.get()))
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            self.log_queue.put(f"间隔配置已更新 - 轮询间隔: {check_interval}秒, 好友检查间隔: {friend_colddown_time}秒, 种植检查间隔: {plant_seed_check_interval}秒")
            messagebox.showinfo("成功", "间隔配置已保存！下次启动机器人时生效。")
            
        except ValueError as e:
            messagebox.showerror("错误", f"请输入有效的数字：{str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{str(e)}")
    
    def start_bot(self):
        """启动机器人"""
        if self.is_running:
            return
        
        try:
            # 重新读取配置
            self.config.read(self.config_path, encoding="utf-8")
            
            # 获取配置参数
            check_interval = self.config.getfloat('bot', 'check_interval')
            debug_mode = self.config.getboolean('bot', 'debug_mode')
            
            # 创建机器人实例
            self.bot = FarmBotCV(check_interval, debug_mode, self.config)

            if self.bot.enable_hide_window and not self.enable_silence_click_var.get():
                self.enable_silence_click_var.set(True)
            
            # 替换机器人的日志处理器
            for handler in self.bot.logger.handlers[:]:
                self.bot.logger.removeHandler(handler)
            
            log_handler = LogHandler(self.log_queue)
            log_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            log_handler.setFormatter(formatter)
            self.bot.logger.addHandler(log_handler)
            
            # 启动机器人在单独线程中
            self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            self.bot_thread.start()
            
            self.is_running = True
            self.is_paused = False
            
            # 更新按钮状态
            self.start_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_var.set("状态: 运行中")
            
            # 禁用全局配置复选框和间隔配置
            self.disable_global_config_checkboxes()
            self.disable_interval_config()
            
            self.log_queue.put("机器人已启动")
            
        except Exception as e:
            self.log_queue.put(f"启动失败: {str(e)}")
            import traceback
            self.log_queue.put(traceback.format_exc())
    
    def run_bot(self):
        """运行机器人（在线程中）"""
        try:
            self.bot.start()
        except Exception as e:
            self.log_queue.put(f"机器人运行错误: {str(e)}")
            import traceback
            self.log_queue.put(traceback.format_exc())
        finally:
            self.is_running = False
            self.root.after(0, self.on_bot_stopped)
    
    def on_bot_stopped(self):
        """机器人停止后的处理"""
        if self.bot:
            self.bot.apply_window_visibility(False)
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("状态: 已停止")
        self.enable_global_config_checkboxes()
        self.enable_interval_config()
    
    def toggle_pause(self):
        """切换暂停/恢复状态"""
        if not self.bot:
            return
        
        if self.is_paused:
            # 恢复
            self.bot.pause_status = False
            self.is_paused = False
            self.pause_btn.config(text="暂停")
            self.status_var.set("状态: 运行中")
            self.log_queue.put("机器人已恢复运行")
        else:
            # 暂停
            self.bot.pause_status = True
            self.is_paused = True
            self.pause_btn.config(text="恢复")
            self.status_var.set("状态: 已暂停")
            self.log_queue.put("机器人已暂停")
    
    def stop_bot(self):
        """停止机器人"""
        if not self.bot:
            return
        
        self.bot.running = False
        self.is_running = False
        self.bot.apply_window_visibility(False)
        self.log_queue.put("正在停止机器人...")
        
        # 等待线程结束
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=3)
        
        self.on_bot_stopped()
    
    def on_config_change(self):
        """配置改变时保存到文件"""
        if self.is_running:
            # 如果机器人正在运行，实时更新配置
            self.update_bot_config()
        else:
            # 否则只保存到配置文件
            self.save_config_to_file()
    
    def update_bot_config(self):
        """更新运行中的机器人配置"""
        if not self.bot:
            return
        
        try:
            # 更新自家农场功能
            self.bot.enable_process_self = self.enable_process_self_var.get()
            self.bot.enable_harvest = self.enable_harvest_var.get()
            self.bot.enable_watering = self.enable_watering_var.get()
            self.bot.enable_remove_grass = self.enable_remove_grass_var.get()
            self.bot.enable_remove_bug = self.enable_remove_bug_var.get()
            self.bot.enable_daily_free = self.enable_daily_free_var.get()
            self.bot.enable_plant_seed = self.enable_plant_seed_var.get()
            
            # 更新好友农场功能
            self.bot.enable_process_friend = self.enable_process_friend_var.get()
            self.bot.enable_steal = self.enable_steal_var.get()
            self.bot.enable_help_watering = self.enable_help_watering_var.get()
            self.bot.enable_help_remove_grass = self.enable_help_remove_grass_var.get()
            self.bot.enable_help_remove_bugs = self.enable_help_remove_bugs_var.get()
            
            # 更新全局配置
            self.bot.enable_silence_click = self.enable_silence_click_var.get()
            self.bot.enable_hide_window = self.enable_hide_window_var.get()

            if self.bot.enable_hide_window and not self.bot.enable_silence_click:
                self.bot.enable_silence_click = True
                self.enable_silence_click_var.set(True)
                self.log_queue.put("已自动开启后台静默点击，以保证隐藏窗口时仍可后台操作")
            
            # 同步更新窗口控制
            if (self.bot.enable_silence_click or self.bot.enable_hide_window) and self.bot.window_control is None:
                from utils.window_control import WindowControl
                self.bot.window_control = WindowControl("QQ经典农场", self.bot.window_session)
            elif not self.bot.enable_silence_click and not self.bot.enable_hide_window and self.bot.window_control is not None:
                self.bot.window_control = None

            self.bot.apply_window_visibility(self.bot.enable_hide_window)
            
            self.log_queue.put("配置已实时更新")
            
        except Exception as e:
            self.log_queue.put(f"更新配置失败: {str(e)}")
        
        # 同时保存到文件
        self.save_config_to_file()
    
    def save_config_to_file(self):
        """保存配置到文件"""
        try:
            if self.enable_hide_window_var.get() and not self.enable_silence_click_var.get():
                self.enable_silence_click_var.set(True)

            # 更新配置对象
            self.config.set('bot', 'enable_process_self', str(self.enable_process_self_var.get()))
            self.config.set('bot', 'enable_process_friend', str(self.enable_process_friend_var.get()))
            self.config.set('bot', 'enable_silence_click', str(self.enable_silence_click_var.get()))
            self.config.set('bot', 'enable_hide_window', str(self.enable_hide_window_var.get()))
            
            self.config.set('self', 'enable_harvest', str(self.enable_harvest_var.get()))
            self.config.set('self', 'enable_watering', str(self.enable_watering_var.get()))
            self.config.set('self', 'enable_remove_grass', str(self.enable_remove_grass_var.get()))
            self.config.set('self', 'enable_remove_bug', str(self.enable_remove_bug_var.get()))
            self.config.set('self', 'enable_daily_free', str(self.enable_daily_free_var.get()))
            self.config.set('self', 'enable_plant_seed', str(self.enable_plant_seed_var.get()))
            
            self.config.set('friend', 'enable_steal', str(self.enable_steal_var.get()))
            self.config.set('friend', 'enable_help_watering', str(self.enable_help_watering_var.get()))
            self.config.set('friend', 'enable_help_remove_grass', str(self.enable_help_remove_grass_var.get()))
            self.config.set('friend', 'enable_help_remove_bugs', str(self.enable_help_remove_bugs_var.get()))
            
            # 写入文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
        except Exception as e:
            self.log_queue.put(f"保存配置失败: {str(e)}")
    
    def disable_global_config_checkboxes(self):
        """禁用全局配置复选框（运行时不允许修改）"""
        self.enable_process_self_cb.config(state=tk.DISABLED)
        self.enable_process_friend_cb.config(state=tk.DISABLED)
        self.enable_silence_click_cb.config(state=tk.DISABLED)
        self.enable_daily_free_cb.config(state=tk.DISABLED)
        self.enable_plant_seed_cb.config(state=tk.DISABLED)
    
    def enable_global_config_checkboxes(self):
        """启用全局配置复选框"""
        self.enable_process_self_cb.config(state=tk.NORMAL)
        self.enable_process_friend_cb.config(state=tk.NORMAL)
        self.enable_silence_click_cb.config(state=tk.NORMAL)
        self.enable_daily_free_cb.config(state=tk.NORMAL)
        self.enable_plant_seed_cb.config(state=tk.NORMAL)
    
    def disable_interval_config(self):
        """禁用间隔配置（运行时不允许修改）"""
        self.check_interval_entry.config(state=tk.DISABLED)
        self.friend_colddown_time_entry.config(state=tk.DISABLED)
        self.plant_seed_check_interval_entry.config(state=tk.DISABLED)
    
    def enable_interval_config(self):
        """启用间隔配置"""
        self.check_interval_entry.config(state=tk.NORMAL)
        self.friend_colddown_time_entry.config(state=tk.NORMAL)
        self.plant_seed_check_interval_entry.config(state=tk.NORMAL)
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_running:
            self.stop_bot()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        img = tk.PhotoImage(file=r"assert\datasets\gui_icon.png")
        root.iconphoto(True, img)
    except Exception as e:
        print(f"加载GUI窗口图标失败，将使用默认图标: {e}")

    app = FarmBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()