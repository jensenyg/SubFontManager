

class StatusBar:
    """状态栏类"""
    labelWidget = None
    timer = None

    @classmethod
    def setLabel(cls, labelWidget):
        """设定一个Label控件用于显示文字"""
        cls.labelWidget = labelWidget

    @classmethod
    def set(cls, text: str = None, duration: int = -1):
        """
        设置状态栏文字
        :param text: 文字
        :param duration: 持续时间，超过该时间后状态栏将清空。>0：时间，=0：无动作，保持原来的计时，-1：持续时间设定为永远。
        """
        cls.labelWidget.config(text=text)
        if duration != 0 and cls.timer:
            cls.labelWidget.after_cancel(cls.timer)
            cls.timer = None
        if duration > 0:
            cls.timer = cls.labelWidget.after(duration * 1000, cls.clear)

    @classmethod
    def append(cls, text: str, duration: int = -1):
        """
        将文字追加到状态栏中
        :param text: 文字
        :param duration: 持续时间，超过该时间后状态栏将清空。>0：时间，=0：无动作，保持原来的计时，-1：持续时间设定为永远。
        """
        cls.set(cls.labelWidget.cget('text') + text, duration)

    @classmethod
    def clear(cls):
        """清空状态栏中的文字"""
        cls.labelWidget.config(text='')
        if cls.timer:
            cls.labelWidget.after_cancel(cls.timer)
            cls.timer = None
