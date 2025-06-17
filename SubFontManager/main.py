from tkinterdnd2 import TkinterDnD
from utils import App
from ui import placeWindow
from window import MainWindow


def onDestroy(event):
    if event.widget is not root:    # Destroy事件也会从所有子控件冒泡上浮，需要筛选响应
        return
    # 保存窗口位置
    _window_rect = (root.winfo_x(), root.winfo_y(), root.winfo_width(), root.winfo_height())
    _window_rect = (int(x / App.dpiScale) for x in _window_rect)
    App.Config.set('General', 'window_x', next(_window_rect))
    App.Config.set('General', 'window_y', next(_window_rect))
    App.Config.set('General', 'window_width', next(_window_rect))
    App.Config.set('General', 'window_height', next(_window_rect))
    App.Config.save()


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    # 设置窗口大小和位置
    window_rect = (App.Config.get('General', 'window_x', None),
                   App.Config.get('General', 'window_y', None),
                   App.Config.get('General', 'window_width', 800),
                   App.Config.get('General', 'window_height', 500))
    window_rect = (int(x) * App.dpiScale if x else None for x in window_rect)
    placeWindow(root, *window_rect, yRatio=0.35)
    root.minsize(int(400*App.dpiScale), int(300*App.dpiScale))
    root.title(App.name)

    mainWindow = MainWindow(root)

    # mainWindow.fileEntryText.set('test.ass')
    # root.after(1000, mainWindow.onLoadBtn)

    root.bind("<Destroy>", onDestroy, add='+')
    root.mainloop()
