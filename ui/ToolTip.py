import tkinter as tk
from App import App


class ToolTip:
    """气泡提示类，用于为控件添加鼠标悬浮的气泡提示"""
    show_delay = 1000  # 气泡显示延迟时间

    def __init__(self, master, text):
        self.master = master
        self.text = text
        self.tip_window = None
        self.after_id = None
        self.master.bind("<Enter>", self.scheduleShow, add='+')
        self.master.bind("<Leave>", self.hideTip, add='+')

    def scheduleShow(self, event):
        self.unscheduleShow()  # 如果之前有计划任务，取消它
        self.after_id = self.master.after(self.show_delay, self.showTip)  # 延迟后显示提示

    def unscheduleShow(self):
        if self.after_id:
            self.master.after_cancel(self.after_id)
            self.after_id = None

    def showTip(self):
        if self.tip_window:
            return
        x = self.master.winfo_pointerx() + int(12 * App.dpiScale)
        y = self.master.winfo_pointery() + int(18 * App.dpiScale)
        self.tip_window = tk.Toplevel(self.master)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip_window, text=self.text, justify='left', background="#ffffe0", borderwidth=1, relief='solid') \
            .pack(ipadx=2)

    def hideTip(self, event=None):
        self.unscheduleShow()  # 鼠标离开时取消计划任务
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
