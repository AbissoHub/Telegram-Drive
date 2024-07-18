def rename_file(original_string, new_first_substring):
    substrings = original_string.split('@')
    substrings[0] = new_first_substring
    return '@'.join(substrings)


def move_file(original_string, new_second_substring):
    substrings = original_string.split('@')
    substrings[1] = new_second_substring
    return '@'.join(substrings)
