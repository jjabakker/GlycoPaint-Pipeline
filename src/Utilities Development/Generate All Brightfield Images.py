import os

from src.Application.Process_Projects.Convert_BF_from_nd2_to_jpg import convert_bf_images


def generate_directory_tree_third_level_directories_only(start_path, output_file, target_level=3):
    with open(output_file, 'w') as f:
        for root, dirs, files in os.walk(start_path):
            # Calculate the depth of the current directory
            level = root.replace(start_path, '').count(os.sep) + 1

            # Only include directories at the target level
            if level == target_level:
                indent = ' ' * 4 * (level - 1)
                f.write(f"{indent}{os.path.basename(root)}/\n")


# Usage
# generate_directory_tree_third_level_directories_only('/Users/hans/Paint Source', 'directory_tree.txt')


new_probes = [
    240924,
    240923,
    241029,
    240812
]

regular_probes = [
    240104,
    230424,
    230412,
    240731,
    240422,
    221012,
    240423,
    230117,
    230126,
    230516,
    240116,
    221129,
    240325,
    230417,
    221101,
    221108,
    230613,
    230419,
    230214,
    230418,
    241029,
    230411,
    240416,
    240814,
    230509,
    230531,
    240807,
    240402,
    230523,
    230321,
    221122,
    230405,
    230608,
    230801
]

# for experiment in new_probes:
#     convert_bf_images(os.path.join('/Volumes/Extreme Pro/Omero', str(experiment)),
#                       os.path.join('/Users/hans/Paint Source/New Probes', str(experiment), 'Brightfield Images'))


for experiment in regular_probes:
    convert_bf_images(os.path.join('/Volumes/Extreme Pro/Omero', str(experiment)),
                      os.path.join('/Users/hans/Paint Source/Regular Probes/', str(experiment)))
