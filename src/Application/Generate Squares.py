import tkinter as tk

from src.Application.Generate_Squares.Generate_Squares_Dialog import GenerateSquaresDialog
from src.Application.Utilities.General_Support_Functions import set_application_icon

if __name__ == "__main__":
    root = tk.Tk()
    root = set_application_icon()
    root.eval('tk::PlaceWindow . center')
    GenerateSquaresDialog(root)
    root.mainloop()
