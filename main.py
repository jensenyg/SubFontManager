from tkinterdnd2 import TkinterDnD
from MainUI import MainUI


def place_window(window, width=500, height=400, xRatio=0.5, yRatio=0.5):
    # 获取屏幕宽高
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    # 计算窗口左上角位置
    x = int((screen_width - width) * xRatio)
    y = int((screen_height - height) * yRatio)
    # 设置窗口大小和位置
    root.geometry(f'{width}x{height}+{x}+{y}')


if __name__ == "__main__":
    # UI配置 -----------------------
    root = TkinterDnD.Tk()
    root.title("Ass Font Embedder")
    root.minsize(400, 300)
    place_window(root, 500, 400, yRatio=0.35)
    mainUI = MainUI(root)
    root.mainloop()
