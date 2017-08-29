package copyjumpvm;

import java.util.ArrayList;

/*
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
*/
public class BitPrinter {
    private ArrayList<Integer> outputSequence;
    BitPrinter(){
        outputSequence = new ArrayList<Integer>();
    }
    void printBit(int outputBit){
        assert outputBit==0 || outputBit==1;
        outputSequence.add(outputBit);
        int outputByte;
        if(outputSequence.size()==8) {
            outputByte = 0;
            int pos = 1;
            for (int iterationBit : outputSequence) {
                outputByte += pos * iterationBit;
                pos *= 2;
            }
            System.out.println("byte:" + outputByte);
            outputSequence.clear();
        }
    }
}
