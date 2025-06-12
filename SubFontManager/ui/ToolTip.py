import tkinter as tk
from utils import App


class ToolTip:
    """气泡提示类，用于为控件添加鼠标悬浮的气泡提示"""
    ShowDelay = 1000  # 气泡显示延迟时间

    def __init__(self, master: tk.Widget, text: str):
        self.master = master
        self.text = text
        self._tipWindow = None
        self._afterId = None
        self.master.bind("<Enter>", self._scheduleShow, add='+') # 为父控件绑定光标进入事件
        self.master.bind("<Leave>", self._hideTip, add='+')  # 为父控件绑定光标离开事件

    def _scheduleShow(self, event):
        """延迟后显示气泡"""
        self._unscheduleShow()  # 如果之前有计划任务，取消它
        self._afterId = self.master.after(self.ShowDelay, self._showTip)  # 延迟后显示提示

    def _unscheduleShow(self):
        """取消显示气泡"""
        if self._afterId:
            self.master.after_cancel(self._afterId)
            self._afterId = None

    def _showTip(self):
        """显示气泡"""
        if self._tipWindow:
            return
        x = self.master.winfo_pointerx() + int(12 * App.dpiScale)
        y = self.master.winfo_pointery() + int(18 * App.dpiScale)
        self._tipWindow = tk.Toplevel(self.master)
        self._tipWindow.wm_overrideredirect(True)
        self._tipWindow.wm_geometry(f"+{x}+{y}")
        tk.Label(self._tipWindow, text=self.text, justify=tk.LEFT,
                 background="#ffffe0", borderwidth=1, relief=tk.SOLID).pack(ipadx=2)

    def _hideTip(self, event=None):
        """删掉气泡"""
        self._unscheduleShow()  # 鼠标离开时取消计划任务
        if self._tipWindow:
            self._tipWindow.destroy()
            self._tipWindow = None

    def destroy(self):
        self.master.unbind("<Enter>")
        self.master.unbind("<Leave>")
