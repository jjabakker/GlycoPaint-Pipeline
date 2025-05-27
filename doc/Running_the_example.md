# Running the example

## Download the data

- Download the demo data from: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14196381.svg)](https://doi.org/10.5281/zenodo.14196381).
A file 'images.zip' (22 GB) will be created in your default download location. It may take an hour or so for the download to complete.
- The zip file may be unpacked automatically (and an 'Images' directory created), but if not, unpack manually and move the images directory to a suitable location. In the example, the images are stored in c:/Users/Hans/Paint Demo Set/Images. There are two experiments: 240104 and 240116.

## Create the Experiment Info file and provide metadata

- In PyCharm, run the 'Prepare Experiments Info' script for each of the two experiments (you'll find it under GlycoPaint -> src -> Application -> Prepare Experiment Info). Set the 'Image Source Directory' to the directory where you just stored the images and specify the first experiment directory, i.e., 240104. For the 'Experiment Directory' select a new empty directory (which you will have created already). Do this for both Experiments (i.e., 240104 and 240116). In the example, the Experiment directories are created in c:/Users/Hans/Paint Demo Set/Paint Demo. There are two experiment directories, 240104 and 240116.
- Open the two Experiment Info files in Excel and provide the metadata (e.g., Probe, Probe Type, Cell Type Adjuvant, Concentration). Repeat the process for the other Experiment Directory. You can download already filled-in versions of these files, [240104 Experiment Info](https://raw.githubusercontent.com/Leiden-chemical-immunology/GlycoPaint/refs/heads/main/Demo/240104%20Experiment%20Info.csv) and [240116 Experiment Info ](https://raw.githubusercontent.com/Leiden-chemical-immunology/GlycoPaint/refs/heads/main/Demo/240116%20Experiment%20Info.csv) and save them in their respective directories as 'Experiment Info.csv'.

## Run TrackMate

- To run TrackMate you have to start Fiji. You then run GlycoPaint by selecting 'GlycoPaint' in the top level menu bar and selecting 'Run TrackMate'.
- For the 'Images Directory' you choose the location where you stored the images (be sure to specify an Experiment, e.g., c:/Users/Hans/Paint Demo Set/Images/240104) and for the 'Experiment Directory' the directory where you stored the corresponding 'Experiment Info' file, e.g., c:/Users/Hans/Paint Demo Set/Paint Demo/240104. Run TrackMate also for the 240116 experiment.

## Generate Squares

- To overlay the squares and calculate square properties, run the Python script 'Generate Squares' from PyCharm (you'll find it under GlycoPaint -> src -> Application -> Generate Squares). You can specify either the individual Experiment Directories, or the Project Directory above it.  

## Compile Project

- To combine the data of all experiments in the project into one data set run the run the Python script 'Compile Project' from PyCharm (you'll find it under GlycoPaint -> src -> Application -> Compile Project). In this case you do need to specify the Project Directory (i.e., c:/Users/Hans/Paint Demo Set/Paint Demo).
- The resulting files, All Recordings, All Squares, All Tracks can be downloaded can be downloaded for reference, [All Recordings](https://raw.githubusercontent.com/Leiden-chemical-immunology/GlycoPaint/refs/heads/main/Demo/All%20Recordings.csv) and [All Squares](https://raw.githubusercontent.com/Leiden-chemical-immunology/GlycoPaint/refs/heads/main/Demo/All%20Squares.csv) and [All Tracks](https://raw.githubusercontent.com/Leiden-chemical-immunology/GlycoPaint/refs/heads/main/Demo/All%20Tracks.csv)

## Inspect the results

- To see how the squares are overlaid over the recordings, you can run the 'Recording Viewer' from PyCharm (GlycoPaint -> src -> Application -> Recording Viewer). You can specify either individual Experiment directories or the Project directory to view recordings of all experiments.

## Generate Figures

- Three files have been generated: 'All Recordings', 'All Squares' and 'All Tracks'. An example Rmd script called   [Demo case.rmd](https://raw.githubusercontent.com/Leiden-chemical-immunology/GlycoPaint/refs/heads/main/Demo/Demo%20case.rmd) is included in the Demo directory. You can run that script in RStudio to generate some example figures. Note that you will have to edit the root_directory to make it point to the directory where the three files are stored. 