from tkinter import *

import pandas as pd


def display_selected_squares(self):
    """
    Display the squares on the left image canvas, that have the 'Selected' flag set
    :return:
    """

    nr_of_squares_in_row = self.nr_of_squares_in_row

    # Clear the screen and reshow the picture
    self.left_image_canvas.delete("all")
    self.left_image_canvas.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])

    # Bind left buttons for canvas
    self.left_image_canvas.bind('<Button-1>', lambda e: self.start_rectangle(e))
    self.left_image_canvas.bind('<ButtonRelease-1>', lambda e: self.close_rectangle(e))
    self.left_image_canvas.bind('<B1-Motion>', lambda e: self.expand_rectangle_size(e))

    if not self.show_squares or len(self.df_squares) == 0:
        return

    # If there are no squares, or if squares are not to be shown, you can stop here
    if len(self.df_squares) == 0:
        return

    i = 1

    # First draw the squares that are selected
    for index, row_in_squares in self.df_squares.iterrows():
        if row_in_squares['Selected']:
            draw_single_square(
                self.show_squares_numbers,
                self.nr_of_squares_in_row,
                self.left_image_canvas,
                row_in_squares,
                self.square_assigned_to_cell,
                self.provide_information_on_square)

    # Then draw the squares that are in the rectangle drawn by the uses(if any)
    for square_nr in self.squares_in_rectangle:
        col_nr = square_nr % nr_of_squares_in_row
        row_nr = square_nr // nr_of_squares_in_row
        width = 512 / nr_of_squares_in_row
        height = 512 / nr_of_squares_in_row

        # Draw the outline without filling the rectangle
        self.left_image_canvas.create_rectangle(
            col_nr * width,
            row_nr * width,
            col_nr * width + width,
            row_nr * height + height,
            outline='white',
            fill="",
            width=3)


def draw_single_square(
        show_squares_numbers,
        nr_of_squares_in_row,
        canvas,
        squares_row,
        square_assigned_to_cell,
        provide_information_on_square):
    """
    :param show_squares_numbers: a boolean tos specify if a number is shown
    :param nr_of_squares_in_row: Show the square numbers in the squares
    :param canvas: the canvas to draw the square on
    :param squares_row: the record containing the information on the square
    :param square_assigned_to_cell: A function to call when a square is assigned to a cell
    :param provide_information_on_square: A function to call when information on a square is requested
:   return:
    """

    colour_table = {1: ('red', 'white'),
                    2: ('yellow', 'black'),
                    3: ('green', 'white'),
                    4: ('magenta', 'white'),
                    5: ('cyan', 'black'),
                    6: ('black', 'white')}

    # Extract the information from the record
    square_nr = squares_row['Square Nr']
    cell_id = squares_row['Cell Id']
    label_nr = squares_row['Label Nr']
    label_nr = 0 if pd.isna(label_nr) else int(squares_row['Label Nr'])
    col_nr = square_nr % nr_of_squares_in_row
    row_nr = square_nr // nr_of_squares_in_row
    width = 512 / nr_of_squares_in_row
    height = 512 / nr_of_squares_in_row

    square_tag = f'square-{square_nr}'
    text_tag = f'text-{square_nr}'

    if cell_id == -1:  # The square is deleted (for good), stop processing    # ToDo Really? Who sets it to -1?
        return

    if cell_id != 0:  # The square is assigned to a cell, so it should be filled with the colour of the cell
        col = colour_table[squares_row['Cell Id']][0]
        canvas.create_rectangle(
            col_nr * width,
            row_nr * width,
            col_nr * width + width,
            row_nr * height + height,
            outline=col,
            fill=col,
            width=0,
            tags=square_tag)

        # Show the cell number in the square
        if show_squares_numbers:
            if not pd.isna(squares_row['Label Nr']):
                canvas.create_text(
                    col_nr * width + 0.5 * width,
                    row_nr * width + 0.5 * width,
                    text=str(label_nr),
                    font=('Arial', -10),
                    fill=colour_table[squares_row['Cell Id']][1],
                    tags=text_tag
                )

    if label_nr == 0:  # The square is selected but does not have a valid Tau: give it a colour
        col = colour_table[squares_row['Square Nr'] % 6 + 1][0]
        canvas.create_rectangle(
            col_nr * width,
            row_nr * width,
            col_nr * width + width,
            row_nr * height + height,
            outline='white',
            fill='#4566A5',  # https://www.webfx.com/web-design/color-picker/4566a5
            width=0,
            tags=square_tag)

    # For all the selected squares, assigned to a cell or not draw the outline without filling the rectangle
    canvas.create_rectangle(
        col_nr * width,
        row_nr * width,
        col_nr * width + width,
        row_nr * height + height,
        outline="white",
        fill="",
        width=1,
        tags=square_tag)

    if show_squares_numbers:
        if cell_id != 0:
            # The number of a square assigned to a cell should not be overwritten
            pass
        else:
            if not pd.isna(squares_row['Label Nr']):
                canvas.create_text(
                    col_nr * width + 0.5 * width,
                    row_nr * width + 0.5 * width,
                    text=str(label_nr),
                    font=('Arial', -10),
                    fill='white',
                    tags=text_tag)

    # Always create a transparent rectangle (clickable area) and bind events to the it
    invisible_rect = canvas.create_rectangle(
        col_nr * width,
        row_nr * width,
        col_nr * width + width,
        row_nr * height + height,
        outline="",
        fill="",
        tags=f"invisible-{square_nr}")
    canvas.tag_bind(invisible_rect, '<Button-1>', lambda e: square_assigned_to_cell(square_nr))
    canvas.tag_bind(invisible_rect, '<Button-2>',
                    lambda e: provide_information_on_square(e, squares_row['Label Nr'], square_nr))
