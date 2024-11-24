from tkinter import *
from tkinter import filedialog, messagebox
from tkinter import ttk

from src.Application.Process_Projects.Convert_BF_from_nd2_to_jpg import convert_bf_images
from src.Application.Utilities.General_Support_Functions import set_application_icon


class ConvertDialog:

    def __init__(self, root):
        self.root = root
        self.root.title('Convert BF Images from native format to .jpg')

        self.image_directory = ""
        self.paint_directory = ""

        content = ttk.Frame(self.root)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Fill the button frame
        btn_process = ttk.Button(frame_buttons, text='Convert', command=self.on_convert)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.on_exit_dialog)
        btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        # Fill the directory frame
        btn_image_dir = ttk.Button(frame_directory, text='Image Source Directory', width=20,
                                   command=self.on_change_image_dir)
        self.lbl_image_dir = ttk.Label(frame_directory, text=self.image_directory, width=50)

        btn_paint_dir = ttk.Button(frame_directory, text='Experiment Directory', width=20,
                                   command=self.on_change_paint_dir)
        self.lbl_paint_dir = ttk.Label(frame_directory, text=self.paint_directory, width=50)

        btn_image_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_image_dir.grid(column=1, row=0, padx=20, pady=5)

        btn_paint_dir.grid(column=0, row=1, padx=10, pady=5)
        self.lbl_paint_dir.grid(column=1, row=1, padx=20, pady=5)

    def on_change_image_dir(self):
        self.image_directory = filedialog.askdirectory(initialdir=self.image_directory)
        if len(self.image_directory) != 0:
            self.lbl_image_dir.config(text=self.image_directory)

    def on_change_paint_dir(self):
        self.paint_directory = filedialog.askdirectory(initialdir=self.paint_directory)
        if len(self.paint_directory) != 0:
            self.lbl_paint_dir.config(text=self.paint_directory)

    def on_convert(self):
        if self.image_directory == "" or self.paint_directory == "":
            message = 'The image directory needs to point to where the images are.\n\n'
            message += "The experiment directory is where the 'Experiment Info.csv' file will be placed."
            messagebox.showwarning(title='Warning', message=message)
        else:
            convert_bf_images(self.image_directory, self.paint_directory, force=False)

    def on_exit_dialog(self):
        self.root.destroy()


if __name__ == '__main__':
    root = Tk()
    root = set_application_icon(root)
    root.eval('tk::PlaceWindow . center')
    ConvertDialog(root)
    root.mainloop()
