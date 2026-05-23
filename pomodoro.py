"""
番茄钟桌面应用 - Pomodoro Timer
基于 Python tkinter，功能完整、界面美观
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import math
import time
import threading
import json
import os
import winsound
from datetime import datetime
import sys


# ─── 配置 ──────────────────────────────────────────────────────────────
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

DEFAULT_CONFIG = {
    "work_time": 25 * 60,        # 25 分钟
    "short_break_time": 5 * 60,  # 5 分钟
    "long_break_time": 15 * 60,  # 15 分钟
    "long_break_interval": 4,    # 每 4 个番茄钟一次长休息
    "daily_goal": 8,             # 每日目标番茄钟数
    "volume": 0.5,               # 音量 0-1
    "always_on_top": True,
    "theme_color": "#E74C3C",    # 番茄红
    "auto_start_break": False,   # 完成后自动开始休息
    "auto_start_work": False,    # 休息后自动开始工作
}

# ─── 样式常量 ──────────────────────────────────────────────────────────
FONT_DIGIT = ("Helvetica", 64, "bold")
FONT_LABEL = ("Helvetica", 14)
FONT_BUTTON = ("Helvetica", 12, "bold")
FONT_SMALL = ("Helvetica", 10)
FONT_TITLE = ("Helvetica", 18, "bold")
FONT_STATUS = ("Helvetica", 16)

COLOR_BG = "#1a1a2e"
COLOR_CARD = "#16213e"
COLOR_ACCENT = "#0f3460"
COLOR_TEXT = "#e8e8e8"
COLOR_TEXT_SECONDARY = "#a0a0b0"
COLOR_BUTTON = "#e94560"
COLOR_BUTTON_HOVER = "#ff6b6b"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f39c12"

CIRCLE_RADIUS = 140
CIRCLE_WIDTH = 12


# ─── 番茄钟主应用 ────────────────────────────────────────────────────
class PomodoroApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("番茄钟 - Pomodoro Timer")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        # 加载配置
        self.config = self.load_config()

        # 状态变量
        self.mode = "work"            # work / short_break / long_break
        self.state = "idle"           # idle / running / paused
        self.time_left = self.config["work_time"]
        self.total_time = self.config["work_time"]
        self.pomodoro_count = 0       # 当前连续完成数
        self.today_count = 0          # 今日完成总数
        self.timer_job = None
        self.start_time = None

        # 设置窗口
        self.setup_window()
        self.create_widgets()
        self.center_window()
        self.update_display()
        self.bind_shortcuts()

        # 加载今日数据
        self.load_today_data()

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ─── 窗口设置 ──────────────────────────────────────────────────
    def setup_window(self):
        w, h = 480, 680
        self.root.geometry(f"{w}x{h}")
        self.root.minsize(w, h)
        self.root.maxsize(w, h)
        if self.config.get("always_on_top", True):
            self.root.attributes("-topmost", True)

        # 设置圆角窗口（需要 Windows 11）
        try:
            from ctypes import windll, c_int, byref
            windll.user32.SetWindowCompositionAttribute(
                windll.kernel32.GetConsoleWindow(),
                20,
                byref(c_int(1))
            )
        except:
            pass

    def center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def bind_shortcuts(self):
        self.root.bind("<space>", lambda e: self.toggle_timer())
        self.root.bind("<Escape>", lambda e: self.reset_timer())
        self.root.bind("<Control-s>", lambda e: self.show_settings())
        self.root.bind("<Control-q>", lambda e: self.on_closing())

    # ─── 配置管理 ──────────────────────────────────────────────────
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return {**DEFAULT_CONFIG, **cfg}
            except:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def load_today_data(self):
        """加载今日完成数据"""
        data_file = os.path.join(CONFIG_DIR, "history.json")
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                today = datetime.now().strftime("%Y-%m-%d")
                if data.get("date") == today:
                    self.today_count = data.get("count", 0)
            except:
                pass

    def save_today_data(self):
        data_file = os.path.join(CONFIG_DIR, "history.json")
        today = datetime.now().strftime("%Y-%m-%d")
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump({"date": today, "count": self.today_count}, f, ensure_ascii=False)

    # ─── 创建界面 ──────────────────────────────────────────────────
    def create_widgets(self):
        # 主容器
        self.main_frame = tk.Frame(self.root, bg=COLOR_BG)
        self.main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        # ─── 顶部：标题 + 模式指示 ───
        self.title_label = tk.Label(
            self.main_frame, text="🍅 番茄钟", font=FONT_TITLE,
            bg=COLOR_BG, fg=COLOR_TEXT
        )
        self.title_label.pack(pady=(0, 5))

        self.mode_label = tk.Label(
            self.main_frame, text="", font=FONT_STATUS,
            bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY
        )
        self.mode_label.pack(pady=(0, 10))

        # ─── 进度指示器（圆环） ───
        self.canvas_frame = tk.Frame(self.main_frame, bg=COLOR_BG)
        self.canvas_frame.pack(pady=10)

        self.canvas = tk.Canvas(
            self.canvas_frame, width=CIRCLE_RADIUS * 2 + CIRCLE_WIDTH * 2,
            height=CIRCLE_RADIUS * 2 + CIRCLE_WIDTH * 2,
            bg=COLOR_BG, highlightthickness=0
        )
        self.canvas.pack()

        cx = CIRCLE_RADIUS + CIRCLE_WIDTH
        cy = CIRCLE_RADIUS + CIRCLE_WIDTH

        # 背景圆环
        self.canvas.create_oval(
            CIRCLE_WIDTH, CIRCLE_WIDTH,
            CIRCLE_RADIUS * 2 + CIRCLE_WIDTH, CIRCLE_RADIUS * 2 + CIRCLE_WIDTH,
            outline="#2a2a4a", width=CIRCLE_WIDTH, tags="bg_arc"
        )

        # 进度圆环（初始画满）
        self.progress_arc = self.canvas.create_arc(
            CIRCLE_WIDTH, CIRCLE_WIDTH,
            CIRCLE_RADIUS * 2 + CIRCLE_WIDTH, CIRCLE_RADIUS * 2 + CIRCLE_WIDTH,
            start=90, extent=360,
            outline=self.get_theme_color(), width=CIRCLE_WIDTH,
            style="arc", tags="progress_arc"
        )

        # 中间时间文本
        self.time_label = tk.Label(
            self.canvas, text="25:00", font=FONT_DIGIT,
            bg=COLOR_BG, fg=COLOR_TEXT
        )
        self.time_label.place(relx=0.5, rely=0.45, anchor="center")

        self.status_label = tk.Label(
            self.canvas, text="点击开始", font=FONT_LABEL,
            bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY
        )
        self.status_label.place(relx=0.5, rely=0.62, anchor="center")

        # 番茄计数（session dots）
        self.dots_frame = tk.Frame(self.main_frame, bg=COLOR_BG)
        self.dots_frame.pack(pady=(15, 5))
        self.dot_labels = []

        self.progress_text = tk.Label(
            self.main_frame, text="", font=FONT_SMALL,
            bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY
        )
        self.progress_text.pack()
        self.update_dots()

        # ─── 今日进度 ───
        self.goal_frame = tk.Frame(self.main_frame, bg=COLOR_CARD, highlightbackground="#2a2a4a", highlightthickness=1)
        self.goal_frame.pack(fill="x", pady=15, ipady=8)

        goal_inner = tk.Frame(self.goal_frame, bg=COLOR_CARD, padx=15, pady=8)
        goal_inner.pack(fill="x")

        self.goal_label = tk.Label(
            goal_inner, text=f"今日进度: 0 / {self.config['daily_goal']} 个番茄",
            font=FONT_LABEL, bg=COLOR_CARD, fg=COLOR_TEXT_SECONDARY
        )
        self.goal_label.pack(anchor="w")

        # 进度条
        self.progress_bar_canvas = tk.Canvas(
            goal_inner, height=8, bg="#2a2a4a", highlightthickness=0
        )
        self.progress_bar_canvas.pack(fill="x", pady=(5, 0))
        self.progress_bar_fill = self.progress_bar_canvas.create_rectangle(
            0, 0, 0, 8, fill=self.get_theme_color(), width=0, tags="fill"
        )
        self.update_goal_progress()

        # ─── 控制按钮 ───
        self.btn_frame = tk.Frame(self.main_frame, bg=COLOR_BG)
        self.btn_frame.pack(pady=10)

        btn_style = {
            "font": FONT_BUTTON, "border": "0",
            "relief": "flat", "cursor": "hand2",
            "padx": 25, "pady": 10,
        }

        self.start_btn = self.create_button(
            self.btn_frame, "▶  开始", COLOR_BUTTON, self.toggle_timer, **btn_style
        )
        self.start_btn.pack(side="left", padx=5)

        self.reset_btn = self.create_button(
            self.btn_frame, "↺  重置", "#533483", self.reset_timer, **btn_style
        )
        self.reset_btn.pack(side="left", padx=5)

        self.skip_btn = self.create_button(
            self.btn_frame, "跳过", "#2d2d5e", self.skip_phase, **btn_style
        )
        self.skip_btn.pack(side="left", padx=5)

        # ─── 模式切换 ───
        self.mode_frame = tk.Frame(self.main_frame, bg=COLOR_BG)
        self.mode_frame.pack(pady=10)

        mode_btn_style = {
            "font": FONT_BUTTON, "border": "0",
            "relief": "flat", "cursor": "hand2",
            "padx": 20, "pady": 8, "width": 10
        }

        self.work_mode_btn = self.create_button(
            self.mode_frame, "工作", COLOR_BUTTON,
            lambda: self.switch_mode("work"), **mode_btn_style
        )
        self.work_mode_btn.pack(side="left", padx=3)

        self.short_break_btn = self.create_button(
            self.mode_frame, "短休", "#2d6a4f",
            lambda: self.switch_mode("short_break"), **mode_btn_style
        )
        self.short_break_btn.pack(side="left", padx=3)

        self.long_break_btn = self.create_button(
            self.mode_frame, "长休", "#1b4965",
            lambda: self.switch_mode("long_break"), **mode_btn_style
        )
        self.long_break_btn.pack(side="left", padx=3)

        # ─── 底部按钮 ───
        bottom_frame = tk.Frame(self.main_frame, bg=COLOR_BG)
        bottom_frame.pack(side="bottom", fill="x", pady=(5, 0))

        self.settings_btn = self.create_button(
            bottom_frame, "⚙  设置", "#2d2d5e", self.show_settings,
            font=FONT_SMALL, border="0", relief="flat", cursor="hand2",
            padx=15, pady=5
        )
        self.settings_btn.pack(side="left")

        # 快捷键提示
        hint = tk.Label(
            bottom_frame, text="空格=开始/暂停  ESC=重置",
            font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY
        )
        hint.pack(side="right")

    def create_button(self, parent, text, color, command, **kwargs):
        """创建扁平风格按钮"""
        btn = tk.Button(
            parent, text=text, bg=color, fg="white",
            activebackground=self.lighten_color(color),
            activeforeground="white",
            command=command, **kwargs
        )
        return btn

    def lighten_color(self, hex_color, factor=0.3):
        """让颜色变亮"""
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(int(r + (255 - r) * factor), 255)
        g = min(int(g + (255 - g) * factor), 255)
        b = min(int(b + (255 - b) * factor), 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def get_theme_color(self):
        return self.config.get("theme_color", COLOR_BUTTON)

    # ─── 界面更新 ──────────────────────────────────────────────────
    def update_display(self):
        """更新时间显示"""
        mins = self.time_left // 60
        secs = self.time_left % 60
        self.time_label.config(text=f"{mins:02d}:{secs:02d}")

        # 更新圆环进度
        fraction = 1 - (self.time_left / self.total_time) if self.total_time > 0 else 0
        extent = 360 * (1 - fraction)
        self.canvas.itemconfig(
            self.progress_arc,
            extent=extent,
            outline=self.get_theme_color()
        )

        # 更新模式文字
        mode_names = {
            "work": "🎯 专注时间",
            "short_break": "☕ 短休息",
            "long_break": "🌿 长休息"
        }
        self.mode_label.config(text=mode_names.get(self.mode, ""))

        # 更新状态文字
        status_map = {
            "idle": "准备就绪",
            "running": "专注中...",
            "paused": "已暂停"
        }
        if self.state == "running" and self.mode == "work":
            if self.time_left > 5 * 60:
                self.status_label.config(text="保持专注 💪")
            elif self.time_left > 60:
                self.status_label.config(text="加油，快完成了！")
            else:
                self.status_label.config(text="冲刺！")
        elif self.state == "running" and "break" in self.mode:
            self.status_label.config(text="放松一下 😊")
        else:
            self.status_label.config(text=status_map.get(self.state, ""))

        # 更新番茄计数显示
        self.update_dots()
        self.update_goal_progress()

    def update_dots(self):
        """更新番茄点显示"""
        for w in self.dots_frame.winfo_children():
            w.destroy()

        self.dot_labels = []
        interval = self.config["long_break_interval"]
        for i in range(interval):
            # 完成且不是长休息后的复位点
            is_done = i < self.pomodoro_count % interval
            # 如果是长休息完成后的状态，显示全部完成
            if self.pomodoro_count > 0 and i < self.pomodoro_count:
                is_done = True

            dot_color = self.get_theme_color() if is_done else "#2a2a4a"
            dot = tk.Label(
                self.dots_frame, text="●", font=("Helvetica", 18),
                bg=COLOR_BG, fg=dot_color
            )
            dot.pack(side="left", padx=4)
            self.dot_labels.append(dot)

        # 显示番茄数量
        self.progress_text.config(
            text=f"已完成 {self.pomodoro_count} 个番茄 | "
                 f"今日 {self.today_count} 个"
        )

    def update_goal_progress(self):
        """更新今日进度条"""
        goal = self.config["daily_goal"]
        count = self.today_count
        fraction = min(count / goal, 1.0) if goal > 0 else 0
        bar_w = self.progress_bar_canvas.winfo_width() or 400
        fill_w = int(bar_w * fraction)
        self.progress_bar_canvas.coords(self.progress_bar_fill, 0, 0, fill_w, 8)
        self.goal_label.config(text=f"今日进度: {count} / {goal} 个番茄")

    # ─── 核心计时逻辑 ──────────────────────────────────────────────
    def toggle_timer(self):
        if self.state == "idle" or self.state == "paused":
            self.start_timer()
        elif self.state == "running":
            self.pause_timer()

    def start_timer(self):
        self.state = "running"
        self.start_btn.config(text="⏸  暂停", bg="#f39c12")
        self.start_time = time.time()
        self.tick()

    def pause_timer(self):
        self.state = "paused"
        self.start_btn.config(text="▶  继续", bg=COLOR_BUTTON)
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

    def reset_timer(self):
        self.state = "idle"
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.start_btn.config(text="▶  开始", bg=COLOR_BUTTON)
        self.set_mode_time()
        self.update_display()

    def skip_phase(self):
        """跳过当前阶段"""
        if self.state == "idle":
            return
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.state = "idle"
        self.start_btn.config(text="▶  开始", bg=COLOR_BUTTON)
        self.on_timer_complete()

    def tick(self):
        """每秒更新"""
        if self.state != "running":
            return

        elapsed = time.time() - self.start_time
        self.time_left = max(0, self.total_time - int(elapsed))
        self.update_display()

        if self.time_left <= 0:
            self.on_timer_complete()
            return

        self.timer_job = self.root.after(200, self.tick)

    def set_mode_time(self):
        """根据当前模式设置时间"""
        if self.mode == "work":
            self.total_time = self.config["work_time"]
        elif self.mode == "short_break":
            self.total_time = self.config["short_break_time"]
        else:
            self.total_time = self.config["long_break_time"]
        self.time_left = self.total_time

    def switch_mode(self, mode):
        if self.state == "running":
            return  # 运行时不允许切换
        self.mode = mode
        self.set_mode_time()
        self.update_display()
        self.update_dots()

    def on_timer_complete(self):
        """计时完成"""
        self.state = "idle"
        self.start_btn.config(text="▶  开始", bg=COLOR_BUTTON)

        # 播放提示音
        self.play_notification()

        if self.mode == "work":
            # 完成一个番茄
            self.pomodoro_count += 1
            self.today_count += 1
            self.save_today_data()

            # 通知
            self.show_notification("🎉 番茄完成！", "太棒了！休息一下吧 👏")

            # 自动切换到休息
            if self.pomodoro_count % self.config["long_break_interval"] == 0:
                self.mode = "long_break"
            else:
                self.mode = "short_break"

            # 自动开始休息
            if self.config.get("auto_start_break"):
                self.set_mode_time()
                self.root.after(1000, self.start_timer)
            else:
                self.set_mode_time()

        else:
            # 休息结束
            mode_name = "短休息" if "short" in self.mode else "长休息"
            self.show_notification(f"☕ {mode_name}结束", "该继续工作了！加油 💪")
            self.mode = "work"

            # 自动开始工作
            if self.config.get("auto_start_work") and self.pomodoro_count > 0:
                self.set_mode_time()
                self.root.after(1000, self.start_timer)
            else:
                self.set_mode_time()

        self.update_display()

    # ─── 通知 ──────────────────────────────────────────────────────
    def play_notification(self):
        """播放提示音"""
        try:
            freq = 800
            duration = 200
            for _ in range(3):
                winsound.Beep(freq, duration)
                time.sleep(0.1)
        except:
            pass

    def show_notification(self, title, message):
        """显示通知，尝试使用 Windows 原生通知"""
        try:
            from winrt.windows.ui.viewmanagement import ApplicationView
            # 使用 tkinter 的简易通知
            self.show_toast(title, message)
        except:
            self.show_toast(title, message)

    def show_toast(self, title, message):
        """使用 tkinter 弹出通知"""
        top = tk.Toplevel(self.root)
        top.title("")
        top.configure(bg=COLOR_BG)
        top.overrideredirect(True)
        top.attributes("-topmost", True)

        w, h = 320, 120
        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() - h - 10
        if y < 0:
            y = self.root.winfo_y() + self.root.winfo_height() + 10
        top.geometry(f"{w}x{h}+{x}+{y}")

        frame = tk.Frame(top, bg=COLOR_CARD, highlightbackground=self.get_theme_color(), highlightthickness=2)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=title, font=FONT_TITLE, bg=COLOR_CARD, fg=COLOR_TEXT).pack(pady=(15, 5))
        tk.Label(frame, text=message, font=FONT_LABEL, bg=COLOR_CARD, fg=COLOR_TEXT_SECONDARY).pack()

        def fade_out():
            try:
                top.destroy()
            except:
                pass

        top.after(3000, fade_out)

    # ─── 设置对话框 ────────────────────────────────────────────────
    def show_settings(self):
        self.pause_timer()

        settings = tk.Toplevel(self.root)
        settings.title("设置 - Settings")
        settings.configure(bg=COLOR_BG)
        settings.resizable(False, False)
        settings.attributes("-topmost", True)
        settings.grab_set()

        w, h = 400, 450
        sw = settings.winfo_screenwidth()
        sh = settings.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        settings.geometry(f"{w}x{h}+{x}+{y}")

        frame = tk.Frame(settings, bg=COLOR_BG, padx=25, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="⏱ 时间设置（分钟）", font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w", pady=(0, 15))

        # 输入框
        inputs = {}
        fields = [
            ("work_time", "专注时间", self.config["work_time"] // 60, 1, 120),
            ("short_break_time", "短休息", self.config["short_break_time"] // 60, 1, 60),
            ("long_break_time", "长休息", self.config["long_break_time"] // 60, 1, 120),
        ]

        for key, label, val, min_v, max_v in fields:
            row = tk.Frame(frame, bg=COLOR_BG)
            row.pack(fill="x", pady=5)

            tk.Label(row, text=label, font=FONT_LABEL, bg=COLOR_BG, fg=COLOR_TEXT,
                     width=10, anchor="w").pack(side="left")

            var = tk.StringVar(value=str(val))
            sp = tk.Spinbox(
                row, from_=min_v, to=max_v, textvariable=var,
                font=FONT_LABEL, width=5, bg=COLOR_CARD, fg=COLOR_TEXT,
                buttonbackground=COLOR_ACCENT, relief="flat"
            )
            sp.pack(side="left", padx=5)
            inputs[key] = (var, min_v, max_v)

            tk.Label(row, text="分钟", font=FONT_LABEL, bg=COLOR_BG,
                     fg=COLOR_TEXT_SECONDARY).pack(side="left")

        # 间隔设置
        tk.Label(frame, text="", bg=COLOR_BG).pack()
        tk.Label(frame, text="🔄 其他设置", font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w", pady=(0, 10))

        # 长休息间隔
        interval_frame = tk.Frame(frame, bg=COLOR_BG)
        interval_frame.pack(fill="x", pady=5)
        tk.Label(interval_frame, text="长休息间隔", font=FONT_LABEL,
                 bg=COLOR_BG, fg=COLOR_TEXT, width=10, anchor="w").pack(side="left")
        interval_var = tk.StringVar(value=str(self.config["long_break_interval"]))
        tk.Spinbox(
            interval_frame, from_=2, to=8, textvariable=interval_var,
            font=FONT_LABEL, width=5, bg=COLOR_CARD, fg=COLOR_TEXT,
            buttonbackground=COLOR_ACCENT, relief="flat"
        ).pack(side="left", padx=5)
        tk.Label(interval_frame, text="个番茄", font=FONT_LABEL,
                 bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY).pack(side="left")

        # 每日目标
        goal_frame = tk.Frame(frame, bg=COLOR_BG)
        goal_frame.pack(fill="x", pady=5)
        tk.Label(goal_frame, text="每日目标", font=FONT_LABEL,
                 bg=COLOR_BG, fg=COLOR_TEXT, width=10, anchor="w").pack(side="left")
        goal_var = tk.StringVar(value=str(self.config["daily_goal"]))
        tk.Spinbox(
            goal_frame, from_=1, to=24, textvariable=goal_var,
            font=FONT_LABEL, width=5, bg=COLOR_CARD, fg=COLOR_TEXT,
            buttonbackground=COLOR_ACCENT, relief="flat"
        ).pack(side="left", padx=5)

        # 自动开始选项
        auto_break_var = tk.BooleanVar(value=self.config.get("auto_start_break", False))
        auto_work_var = tk.BooleanVar(value=self.config.get("auto_start_work", False))

        tk.Checkbutton(frame, text="完成后自动开始休息", variable=auto_break_var,
                       font=FONT_LABEL, bg=COLOR_BG, fg=COLOR_TEXT,
                       selectcolor=COLOR_CARD, activebackground=COLOR_BG,
                       activeforeground=COLOR_TEXT).pack(anchor="w", pady=2)
        tk.Checkbutton(frame, text="休息后自动开始工作", variable=auto_work_var,
                       font=FONT_LABEL, bg=COLOR_BG, fg=COLOR_TEXT,
                       selectcolor=COLOR_CARD, activebackground=COLOR_BG,
                       activeforeground=COLOR_TEXT).pack(anchor="w", pady=2)

        # 保存按钮
        def save_settings():
            try:
                for key, (var, min_v, max_v) in inputs.items():
                    val = int(var.get())
                    val = max(min_v, min(max_v, val))
                    self.config[key] = val * 60

                self.config["long_break_interval"] = int(interval_var.get())
                self.config["daily_goal"] = int(goal_var.get())
                self.config["auto_start_break"] = auto_break_var.get()
                self.config["auto_start_work"] = auto_work_var.get()

                self.save_config()
                self.set_mode_time()
                self.update_display()
                self.update_dots()
                self.update_goal_progress()
                settings.destroy()
            except ValueError:
                messagebox.showerror("错误", "请输入有效数字")

        save_btn = self.create_button(
            frame, "💾  保存", COLOR_BUTTON, save_settings,
            font=FONT_BUTTON, border="0", relief="flat", cursor="hand2",
            padx=30, pady=8
        )
        save_btn.pack(pady=15)

    # ─── 窗口事件 ──────────────────────────────────────────────────
    def on_closing(self):
        """关闭窗口"""
        if self.state == "running":
            result = messagebox.askyesno("确认", "计时正在进行中，确定要退出吗？")
            if not result:
                return
        self.save_config()
        self.save_today_data()
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


# ─── 启动 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = PomodoroApp()
    app.run()