from src.Application.Support.General_Support_Functions import (concat_csv_files)

def main():

    csv_files = ['/Users/hans/Paint/Paint Sweep Squares/Results/All Recordings - 5.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Recordings - 10.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Recordings - 15.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Recordings - 20.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Recordings - 30.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Recordings - 40.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Recordings - 50.csv']

    concat_csv_files('/Users/hans/Paint/Paint Sweep Squares/Results/All Recordings.csv', csv_files)


    csv_files = ['/Users/hans/Paint/Paint Sweep Squares/Results/All Squares - 5.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Squares - 10.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Squares - 15.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Squares - 20.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Squares - 30.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Squares - 40.csv',
                 '/Users/hans/Paint/Paint Sweep Squares/Results/All Squares - 50.csv']

    concat_csv_files('/Users/hans/Paint/Paint Sweep Squares/Results/All Squares.csv', csv_files)


if __name__ == "__main__":
    main()