from tkinter import ttk


class StatusBar(ttk.Label):
    """状态栏类"""

    def __init__(self, master):
        super().__init__(master)
        self.timer = None

    def set(self, text: str = None, duration: int = -1, override: bool = True):
        """
        设置状态栏文字
        :param text: 文字，''表示清空，None为不变
        :param duration: 持续时间，超过该时间后状态栏将清空。>0：时间，=0：无动作，保持原来的计时，-1：持续时间设定为永远。
        :param override: 是否覆盖当前显示的文字
        """
        if override or not self.cget('text'):
            self.config(text=text)
            if duration != 0 and self.timer:
                self.after_cancel(self.timer)
                self.timer = None
            if duration > 0:
                self.timer = self.after(duration * 1000, self.clear)

    def append(self, text: str, duration: int = -1):
        """
        将文字追加到状态栏中
        :param text: 文字
        :param duration: 持续时间，超过该时间后状态栏将清空。>0：时间，=0：无动作，保持原来的计时，-1：持续时间设定为永远。
        """
        self.set(self.cget('text') + text, duration)

    def clear(self):
        """清空状态栏中的文字"""
        self.config(text='')
        if self.timer:
            self.after_cancel(self.timer)
            self.timer = None
