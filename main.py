from tkinterdnd2 import TkinterDnD
from ui import placeWindow
import __version__
from MainUI import MainUI


if __name__ == "__main__":
    # UI配置 -----------------------
    root = TkinterDnD.Tk()
    root.title(__version__.name)
    root.minsize(400, 300)
    placeWindow(root, 800, 500, yRatio=0.35)
    mainUI = MainUI(root)
    mainUI.fileEntryText.set('/Users/shine/Downloads/Cowboy Bebop S01E01 BDRip 1080p x265-NAHOM.chs.ass')
    # mainUI.onFileEntryInsert()
    mainUI.onLoadBtn()
    root.mainloop()
