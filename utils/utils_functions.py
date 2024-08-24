# Create correct format string to change name of file

import os


def rename_file(original_string, new_first_substring):
    p = original_string.split('@')
    p[0] = new_first_substring
    return '@'.join(p)


# Create correct format string to change path of file
def move_file(original_string, new_second_substring):
    p = original_string.split('@')
    p[1] = new_second_substring
    return '@'.join(p)


def is_file_in_directory(target_directory, file_path):
    target_directory = os.path.abspath(target_directory)
    file_path = os.path.abspath(file_path)
    return file_path.startswith(target_directory)


def get_value_from_string(data_dict, key_to_find):
    # Iterate through the dictionary keys to find the one containing the key_to_find
    for key, value in data_dict.items():
        if key_to_find in key:
            return value

    # If the key is not found, return None
    return None
