import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import tkinter as tk
from gui.app import FireSmokeApp
root=tk.Tk();app=FireSmokeApp(root)
app._source_type.set('Image');app._source_changed()
app._source_var.set(str(Path(__file__).resolve().parent/'fire_original.png'))
app._method_var.set('yolo')
root.after(1500,app.detect_image)
root.mainloop()
