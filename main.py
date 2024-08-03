from tkinterdnd2 import TkinterDnD
from Global import Config, AppInfo
from ui import placeWindow
from MainUI import MainUI


def onDestroy(event):
    global is_destroying
    if is_destroying:   # 窗口关闭时Destroy事件会被触发很多次，只响应一次即可
        return
    is_destroying = True

    # 保存窗口位置
    Config.set('General', 'windowX', root.winfo_x())
    Config.set('General', 'windowY', root.winfo_y())
    Config.set('General', 'windowWidth', root.winfo_width())
    Config.set('General', 'windowHeigh', root.winfo_height())
    Config.save()


if __name__ == "__main__":
    # 窗口配置 -----------------
    root = TkinterDnD.Tk()
    # 设置窗口大小和位置
    window_rect = (Config.get('General', 'windowX', None),  Config.get('General', 'windowY', None),
                   Config.get('General', 'windowWidth', 800), Config.get('General', 'windowHeigh', 500))
    window_rect = (int(x) if x else None for x in window_rect)
    placeWindow(root, *window_rect, yRatio=0.35)
    root.minsize(400, 300)
    root.title(AppInfo.name)

    mainUI = MainUI(root)

    is_destroying = False   # 程序是否已进入关闭流程
    root.bind("<Destroy>", onDestroy, add='+')
    mainUI.fileEntryText.set('/Users/shine/Downloads/Cowboy Bebop S01E01 BDRip 1080p x265-NAHOM.chs.ass')
    mainUI.onLoadBtn()
    root.mainloop()
