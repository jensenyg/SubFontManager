import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from ScrollableFrame import ScrollableFrame
from PlaceholderEntry import PlaceholderEntry
from SubStationAlpha import SubStationAlpha


def open_file():
    filename = filedialog.askopenfilename(
        filetypes=[("Advanced SubStation Alpha", "*.ass"), ("SubStation Alpha", "*.ssa"), ("All files", "*.*")]
    )
    if filename:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, filename)
    root.focus_force()
    on_load_btn()


def open_directory():
    filepath = filedialog.asksaveasfilename(
        initialdir=".",
        initialfile="newsubtitle",
        defaultextension=".ass",
        filetypes=[("Advanced SubStation Alpha", "*.ass"), ("SubStation Alpha", "*.ssa"), ("All files", "*.*")]
    )
    if filepath:
        dir_entry.delete(0, tk.END)
        dir_entry.insert(0, filepath)
    root.focus_force()


def on_drop(event):
    file_path = event.data.strip('{}')
    if not file_path.endswith(('.ass', '.ssa')):
        messagebox.showerror("错误", "仅支持 .ass 和 .ssa 文件")
    file_entry.delete(0, tk.END)
    file_entry.insert(0, event.data)


def on_switchsavemode():
    dir_entry.configure(state=tk.DISABLED if save_mode.get() == 0 else tk.NORMAL)
    save_button.configure(state=tk.DISABLED if save_mode.get() == 0 else tk.NORMAL)


def on_file_entry_insert(*args):
    reload_btn.configure(state=tk.NORMAL if file_entry_text.get() else tk.DISABLED)


def on_file_entry_enter(*args):
    print('on_file_entry_enter')


def on_load_btn(*args):
    path = file_entry_text.get()
    subtitleObj = SubStationAlpha.load(path)
    # fontDict = subtitleObj.gatherFonts()
    subtitleObj.save(dir_entry.get())
    reload_btn.configure(text="重新载入" if subtitleObj else "载入")


def on_ok_btn(event):
    pass


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
    gapy = 2    # 控件垂直间距

    # 文件打开和保存区
    frame1 = ttk.Frame(root)
    frame1.grid(row=0, padx=10, pady=10, sticky="we")

    ttk.Label(frame1, text="输入文件:").grid(row=0, column=0, pady=gapy, sticky="w")
    file_entry_text = tk.StringVar()
    file_entry = ttk.Entry(frame1, textvariable=file_entry_text)
    file_entry.grid(row=0, column=1, columnspan=2, padx=5, sticky="ew")
    file_entry.bind("<Return>", on_file_entry_enter)
    file_entry_text.trace("w", on_file_entry_insert)
    open_btn = tk.Button(frame1, text="...", command=open_file)
    open_btn.grid(row=0, column=3)

    ttk.Label(frame1, text="输出文件:").grid(row=1, column=0, pady=gapy, sticky="w")
    save_mode = tk.IntVar()
    save_mode.set(0)
    ttk.Radiobutton(frame1, text="修改原文件", variable=save_mode, value=0, command=on_switchsavemode)\
        .grid(row=1, column=1, padx=5, sticky="w")

    # "另存为"Frame，包括一个Radio和一个Entry
    saveas_frame = ttk.Frame(frame1)
    saveas_frame.grid(row=2, column=1, columnspan=3, sticky="ew")
    ttk.Radiobutton(saveas_frame, text="另存为:", variable=save_mode, value=1, command=on_switchsavemode)\
        .pack(side='left', padx=5, pady=gapy)
    dir_entry_text = tk.StringVar()
    dir_entry = PlaceholderEntry(saveas_frame, textvariable=dir_entry_text,
                                 placeholder="Leave blank to save to source directory.")
    dir_entry.configure(state=tk.DISABLED)
    dir_entry.pack(side='left', padx=5, fill="x", expand=True)
    save_button = tk.Button(saveas_frame, text="...", state=tk.DISABLED, command=open_directory)
    save_button.pack(side='right')

    # 配置列权重，使输入框能够随窗口大小变化而变化
    frame1.columnconfigure(1, weight=1)

    # "字体列表"Label和"载入"按钮
    frame2 = ttk.Frame(root)
    frame2.grid(row=1, padx=5, sticky="we")
    ttk.Label(frame2, text="字幕中包含的字体:").pack(side='left', padx=5)
    reload_btn = tk.Button(frame2, text="载入", width=6, command=on_load_btn, state=tk.DISABLED)
    reload_btn.pack(side='right', padx=5)

    # 可滚动字体列表
    fontList_frame = ScrollableFrame(root, bg='#FFF', bd=1, relief="sunken")
    fontList_frame.grid(row=2, padx=10, pady=5, sticky="nswe")

    # 在滚动区域内添加复选框
    checkbutton_vars = []
    table_frame = fontList_frame.scrollable_frame
    for i in range(6):  # 共25行，每行两个复选框，共50个复选框
        var1 = tk.BooleanVar(value=(i % 2 == 0))
        check1 = tk.Checkbutton(table_frame, text=f"Checkbutton {i * 2}", variable=var1, bg='#FFF')
        check1.grid(row=i, column=0, pady=1, sticky="w")
        checkbutton_vars.append(var1)

        charcount_label = tk.Label(table_frame, text="1234", bg="#FFF")
        charcount_label.grid(row=i, column=1, padx=5)

        var2 = tk.BooleanVar(value=(i % 2 == 1))
        check2 = tk.Checkbutton(table_frame, text="Subset", variable=var2, bg='#FFF')
        check2.grid(row=i, column=2, padx=(5, 0), pady=1, sticky="e")
        checkbutton_vars.append(var2)
    table_frame.columnconfigure(0, weight=1)

    # 底部的确定和取消按钮区
    button_frame = ttk.Frame(root)
    button_frame.grid(row=3, pady=(5, 10))

    ok_button = ttk.Button(button_frame, text="确定", command=on_ok_btn)
    ok_button.pack(side="left", padx=5)
    cancel_button = ttk.Button(button_frame, text="取消", command=root.destroy)
    cancel_button.pack(side="right", padx=5)

    # 配置列权重，使列表框能够随窗口大小变化而变化
    root.rowconfigure(2, weight=1)
    root.columnconfigure(0, weight=1)

    # 绑定拖放事件到窗口
    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<Drop>>', on_drop)

    root.mainloop()

    # 系统变量 -------------------------
    subtitleObj = None
