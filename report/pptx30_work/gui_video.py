import sys
from pathlib import Path
sys.dont_write_bytecode=True
rootdir=Path(__file__).resolve().parents[2];sys.path.insert(0,str(rootdir))
import tkinter as tk
from gui.app import FireSmokeApp
root=tk.Tk();app=FireSmokeApp(root)
app._source_type.set('Video');app._source_changed();app._source_var.set(str(rootdir/'data/video/253436_medium.mp4'));app._method_var.set('yolo')
root.after(1000,app.start)
root.after(18000,app.stop)
root.mainloop()
