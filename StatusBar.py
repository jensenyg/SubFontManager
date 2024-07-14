import threading


class StatusBar:
    """状态栏类"""
    labelWidget = None
    timer = None

    @classmethod
    def setLabel(cls, labelWidget):
        """设定一个Label用于显示文字"""
        cls.labelWidget = labelWidget

    @classmethod
    def set(cls, text: str = None, duration: int = -1):
        """
        设置状态栏文字
        :param text: 文字
        :param duration: 持续时间，超过该时间后状态栏将清空。>0：时间，=0：无动作，保持原来的计时，-1：持续时间设定为永远。
        """
        cls._runInDeamon(cls._set, text, duration)

    @classmethod
    def _set(cls, text: str = None, duration: int = -1):
        cls.labelWidget.config(text=text)
        cls._setTimer(duration)

    @classmethod
    def append(cls, text: str, duration: int = -1):
        """
        将文字追加到状态栏中
        :param text: 文字
        :param duration: 持续时间，超过该时间后状态栏将清空。>0：时间，=0：无动作，保持原来的计时，-1：持续时间设定为永远。
        """
        cls._runInDeamon(cls._append, text, duration)

    @classmethod
    def _append(cls, text: str, duration: int = -1):
        new_text = cls.labelWidget.cget('text') + text
        cls.labelWidget.config(text=new_text)
        cls._setTimer(duration)

    @classmethod
    def _runInDeamon(cls, func, *args):
        """
        使用守护线程来执行函数
        由于状态栏显示涉及到Timer定时，有可能在程序结束时候阻止结束，因此使用守护线程执行，保证它会跟随主线程一同结束
        """
        t = threading.Thread(target=func, args=args)
        t.daemon = True
        t.start()

    @classmethod
    def _setTimer(cls, duration: int = None):
        if duration != 0 and cls.timer:
            cls.timer.cancel()
        if duration > 0:
            cls.timer = threading.Timer(duration, cls._onTimer)
            cls.timer.start()

    @classmethod
    def _onTimer(cls):
        cls.labelWidget.config(text='')
        cls.timer = None
