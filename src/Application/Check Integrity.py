from tkinter import *

from src.Application.Check_Integrity.Check_Integrity import IntegrityDialog
from src.Application.Support.General_Support_Functions import set_application_icon

root = Tk()
root = set_application_icon(root)
root.eval('tk::PlaceWindow . center')
IntegrityDialog(root)
root.mainloop()
