import tkinter as tk
from tkinter import ttk


class ScrollableFrame(tk.Frame):
    def __init__(self, container, **kwargs):
        super().__init__(container, **kwargs)
        bg = kwargs.get('background', kwargs.get('bg'))

        self.canvas = tk.Canvas(self, bg=bg)
        self.canvas.config(highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮事件
        # Windows and MacOS
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        # Linux
        self.canvas.bind_all("<Button-4>", self.on_mousewheel)
        self.canvas.bind_all("<Button-5>", self.on_mousewheel)

    def on_mousewheel(self, event):
        if self.scrollbar.get() == (0.0, 1.0):
            return
        if event.delta:  # Windows and MacOS
            self.canvas.yview("scroll", -event.delta, "units")
        elif event.num == 4:  # Linux scroll up
            self.canvas.yview("scroll", -1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview("scroll", 1, "units")
