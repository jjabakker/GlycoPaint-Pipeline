from tkinter import *

from src.Application.Compile_Project.Compile_Project import CompileDialog
from src.Application.Utilities.General_Support_Functions import set_application_icon

root = Tk()
root = set_application_icon(root)
root.eval('tk::PlaceWindow . center')
CompileDialog(root)
root.mainloop()
