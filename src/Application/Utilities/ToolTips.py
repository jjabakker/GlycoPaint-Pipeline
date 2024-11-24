import tkinter as tk


class ToolTip:
    def __init__(self, widget, text, wraplength=200):
        self.widget = widget
        self.text = text
        self.wraplength = wraplength  # Set wrap length for the tooltip text
        self.tooltip_window = None

        # Bind the hover events
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        # Create a small window for the tooltip
        if self.tooltip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 20  # Tooltip position offset
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10

        # Create the tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Remove window borders
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Add a label with the tooltip text, set the wrap length for text wrapping
        label = tk.Label(
            self.tooltip_window, text=self.text, background="#f0e68c",  # Softer yellow (Khaki)
            relief="solid", borderwidth=1, font=("Arial", 10), wraplength=self.wraplength,
            anchor="w", justify="left"  # Left-align the text
        )
        label.pack(ipadx=5, ipady=2)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


if __name__ == '__main__':
    def on_button_press():
        print("Button pressed!")


    root = tk.Tk()
    root.title("Button with Tooltip Example")

    # Create a button
    button = tk.Button(root, text="Press Me", command=on_button_press)
    button.grid(row=0, column=0, padx=20, pady=20)

    # Add a tooltip to the button
    ToolTip(button, wraplength=400,
            text="Shortcut: Command+M on macOS or Alt+M on other OS. Or maybe you can add a lot of text. Or maybe you can add a lot of text.Or maybe you can add a lot of text.")

    root.mainloop()
