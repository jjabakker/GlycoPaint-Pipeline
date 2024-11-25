import tkinter as tk

from src.Application.Check_Integrity.Check_integrity_Dialog import CheckIntegrityDialog
from src.Application.Utilities.General_Support_Functions import set_application_icon

if __name__ == "__main__":
    root = tk.Tk()
    root = set_application_icon(root)
    root.eval('tk::PlaceWindow . center')
    CheckIntegrityDialog(root)
    root.mainloop()
