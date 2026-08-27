#!/usr/bin/env python3
'''A bytecode interpreter. Possible instructions are of assignment or jump type.'''

class BitPrinter: # pylint: disable=too-few-public-methods
    '''Prints a bit and a byte.'''
    def __init__(self):
        self.out_sequence = []

    def print_bit(self, output_bit):
        '''Adds a bit to the output.'''

        assert output_bit == 0 or output_bit == 1
        self.out_sequence.append(output_bit)
        print('bit:', output_bit)

        if len(self.out_sequence) == 8:
            output_byte = 0
            pos = 1
            for iter_bit in self.out_sequence:
                output_byte += pos * iter_bit
                pos *= 2
            print('byte:', output_byte)
            self.out_sequence = []

def run_code(code, bit_printer, memory):
    '''Runs some source code.'''

    def init_memory(mem):
        '''Initializes memory.
        #memory[0] = 0 #constant source of zeroes during bit copy (mov)
        #memory[1] = 1 #constant source of ones during bit copy (mov)'''
        return [0, 1] + mem

    mem = init_memory(memory)

    def parse(code):
        '''Parses source code.'''
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
            line = line.split("#")[0] # skip comments (everything after a ';' character)
            line = line.strip() # strip blank characters
            if line == '':
                continue # skip empty lines

            operands = line.split(' ')
            if operands[0] != 'l': # exclude line_labels (lines with label)
                lines.append(line)
            elif operands[0] == 'l':
                line_labels[operands[1]] = len(lines)
        line_labels['end'] = len(lines)
        return lines, line_labels

    lines, line_labels = parse(code)

    def execute(lines, line_labels, bit_printer):
        '''Runs some byte code.'''

        def read(src): # read from address
            '''Reads a bit from an address.'''
            try:
                src = int(src)
                value = mem[src]
            except ValueError:
                if src == 'in':
                    while True:
                        try:
                            value = int(input('bit? '))
                            if value in (0, 1):
                                break
                        except ValueError:
                            pass
            return value

        def write(dst, src, bit_printer): # write to address
            '''Writes a bit copying from source address to destination address.'''
            try:
                dst = int(dst)
                mem[dst] = src
            except ValueError:
                if dst == 'out':
                    bit_printer.print_bit(src)

        def jump(cline, instruction_pointer, line_labels): # pylint: disable=too-many-arguments
            '''Handles Jump instructions.'''
            if len(cline) == 2: # unconditional jump
                new_instruction_pointer = cline[1]

            elif len(cline) == 3: # conditional jump
                bit = read(cline[1])
                assert bit == 0 or bit == 1
                if bit == 0:
                    new_instruction_pointer = 'next'
                elif bit == 1:
                    new_instruction_pointer = cline[2]

            elif len(cline) == 4: # 2-conditional jump
                bit = read(cline[1])
                assert bit == 0 or bit == 1
                if bit == 0:
                    new_instruction_pointer = cline[2]
                elif bit == 1:
                    new_instruction_pointer = cline[3]

            if new_instruction_pointer == 'next':
                instruction_pointer += 1
            else:
                try:
                    instruction_pointer = int(new_instruction_pointer)
                except ValueError:
                    instruction_pointer = line_labels[new_instruction_pointer]

            return instruction_pointer

        executable_lines = list(map(lambda s: s.split(' '), lines))
        instruction_pointer = 0

        while instruction_pointer < len(lines):
            cline = executable_lines[instruction_pointer]

            if cline[0] == 'j': # parse jump

                instruction_pointer = jump(cline, instruction_pointer, line_labels)

            elif cline[0] == 'm': # parse move

                dst, src = cline[1], cline[2]

                got = read(src)
                write(dst, got, bit_printer)
                instruction_pointer += 1

            else:
                print('current line(cline) is not a valid instruction:', cline)

    execute(lines, line_labels, bit_printer)

def run_code_from_string(code_string):
    '''Runs program-code string.'''
    bit_printer = BitPrinter()
    memory = [0 for i in range(1024*8)]
    run_code(code_string, bit_printer, memory)

def run_code_from_argv():
    '''Runs program from a file containg program-code
    whose file-name is provided as CLI argument(argv).'''
    import sys
    if len(sys.argv) != 2:
        print('provide a file-name argument!')
    else:
        file_name = sys.argv[1]
        run_code_from_string(open(file_name).read())

if __name__ == '__main__':
    run_code_from_argv()
