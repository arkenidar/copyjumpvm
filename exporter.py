#!/usr/bin/env python3

"""
Export programs from textual format to numeric format.
"""


def parse_move_field(value):
    """ Parses a move operation instruction field. """
    dictionary = {'in': 3, 'out': 3}
    try:
        value = int(value)
        if value > 1:
            value += 2
    except ValueError:
        value = dictionary[value]
    return value


def parse_jump_field(idx, value, line_labels):
    """ Parses a jump operation instruction field. """
    try:
        value = int(value)
    except ValueError:
        try:
            value = line_labels[value] - idx
        except KeyError:
            if value == 'next':
                value = 1
    return value


def copy_to_path_chooser(copy_from_address):
    """ Build a "copy a bit to path chooser bit" instruction."""
    return [parse_move_field(copy_from_address), 2, 1, 1]


def parse_line(idx, line, line_labels):
    """ Parses line from a string-based format to a integer-based format. """
    copy_from, copy_to = 0, 0
    jump_case_true, jump_case_false = 1, 1

    instruction_before_current = None

    line = line.split(' ')

    if line[0] == 'm':
        copy_from = parse_move_field(line[2])
        copy_to = parse_move_field(line[1])

    elif line[0] == 'j':
        if len(line) == 2:
            destination = parse_jump_field(idx, line[1], line_labels)
            jump_case_true, jump_case_false = destination, destination
        elif len(line) == 3:
            jump_case_true = parse_jump_field(idx, line[2], line_labels)
            jump_case_false = 1
            instruction_before_current = copy_to_path_chooser(line[1])
        elif len(line) == 4:
            jump_case_true = parse_jump_field(idx, line[3], line_labels)
            jump_case_false = parse_jump_field(idx, line[2], line_labels)
            instruction_before_current = copy_to_path_chooser(line[1])

    return [[copy_from, copy_to, jump_case_true, jump_case_false], instruction_before_current]


def parse(code):
    """Parses source code."""
    lines = []
    line_labels = {}
    comment_ignore_mode = False
    for line in code.split('\n'):

        # handles multi-line comments
        # (they begin in a line and end in another line,
        # and the in-between is commented)

        if line.strip() == '#begin:':
            comment_ignore_mode = True
            continue

        if line.strip() == '#end:':
            comment_ignore_mode = False
            continue

        if comment_ignore_mode:
            continue

        # pre-parsing
        line = line.split("#")[0]  # skip comments (everything after a ';' character)
        line = line.strip()  # strip blank characters
        if line == '':
            continue  # skip empty lines

        operands = line.split(' ')
        if operands[0] != 'l':  # exclude line_labels (lines with label)
            lines.append(line)
        elif operands[0] == 'l':
            line_labels[operands[1]] = len(lines)
    line_labels['end'] = len(lines)
    return lines, line_labels


def parsing(file_to_parse):
    """
    :param file_to_parse: file to parse into parsed lines
    :return: parsed lines from program
    """
    lines, line_labels = parse(open(file_to_parse).read())

    parsed_lines = []
    # print('parse lines')
    for idx, line in enumerate(lines):
        parsed_line = parse_line(idx, line, line_labels)
        parsed_lines += [parsed_line]
        # print(parsed_line, line)

    # insertions
    parsed_lines = insertions(parsed_lines)

    return parsed_lines


def insertions(parsed_lines):
    """ Fuses two instructions. """
    parsed_lines_output = []
    for line in parsed_lines:
        if line[1] is not None:
            line = [line[1][0], line[1][1], line[0][2], line[0][3]]
        else:
            line = line[0]
        parsed_lines_output += [line]
    return parsed_lines_output


def output_to_file(parsed_lines, numeric_format_file):
    """
    :param parsed_lines: program lines
    :param numeric_format_file: output file name (numeric format output)
    """
    output_file = open(numeric_format_file, 'w')
    for line in parsed_lines:
        # line = line[0]
        for field_idx, field in enumerate(line):
            try:
                numeric_field = int(field)
            except ValueError:
                if field_idx in (2, 3) and field == 'exit':
                    numeric_field = len(parsed_lines)
                else:
                    raise
            finally:
                output_file.write(str(numeric_field) + " ")
        output_file.write("\n")
    output_file.close()


def main():
    """ Main function. """

    mappings = [
        ['program_not_gate.prg.txt', 'not_gate.cj'],
        ['program_or_gate.prg.txt', 'or_gate.cj'],
        ['program_full_adder.prg.txt', 'full_adder.cj'],
        ['program_integer_counter.prg.txt', 'integer_counter.cj'],
        ['program_integer_sum.prg.txt', 'integer_sum.cj'],
    ]
    for mapping in mappings:
        # parsing
        parsed_lines = parsing(mapping[0])

        # output to file
        output_to_file(parsed_lines, '/home/mint/NetBeansProjects/copyjumpvm/'+mapping[1])

if __name__ == '__main__':
    main()
