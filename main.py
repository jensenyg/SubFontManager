from tkinterdnd2 import TkinterDnD
from App import App
from ui import placeWindow
from MainUI import MainUI


def onDestroy(event):
    global is_destroying
    if is_destroying:   # 窗口关闭时Destroy事件会被触发很多次，只响应一次即可
        return
    is_destroying = True

    # 保存窗口位置
    window_rect = (root.winfo_x(), root.winfo_y(), root.winfo_width(), root.winfo_height())
    window_rect = (int(x / App.dpiScale) for x in window_rect)
    App.Config.set('General', 'windowX', next(window_rect))
    App.Config.set('General', 'windowY', next(window_rect))
    App.Config.set('General', 'windowWidth', next(window_rect))
    App.Config.set('General', 'windowHeigh', next(window_rect))
    App.Config.save()


if __name__ == "__main__":
    # 开启DPI感知
    App.setDpiAwareness()
    # 设置窗口大小和位置
    root = TkinterDnD.Tk()
    window_rect = (App.Config.get('General', 'windowX', None),  App.Config.get('General', 'windowY', None),
                   App.Config.get('General', 'windowWidth', 800), App.Config.get('General', 'windowHeigh', 500))
    window_rect = (int(x) * App.dpiScale if x else None for x in window_rect)
    placeWindow(root, *window_rect, yRatio=0.35)
    root.minsize(int(400*App.dpiScale), int(300*App.dpiScale))
    root.title(App.name)

    mainUI = MainUI(root)

    is_destroying = False   # 程序是否已进入关闭流程
    root.bind("<Destroy>", onDestroy, add='+')
    mainUI.fileEntryText.set('test.ass')
    mainUI.onLoadBtn()
    root.mainloop()
