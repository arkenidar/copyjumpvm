package copyjumpvm;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.LinkedList;
import java.util.Scanner;

public class Instructions {
    LinkedList<CopyJumpInstruction> instructions;
    
    Instructions(String programFilename) throws FileNotFoundException{
        File file = new File(programFilename);
        Scanner scanner = new Scanner(file);
        String nextLine;
        instructions = new LinkedList<CopyJumpInstruction>();
        while(scanner.hasNextInt()){
            instructions.add(
                    new CopyJumpInstruction(
                        new CopyInstruction(scanner.nextInt(), scanner.nextInt()),
                        new JumpInstruction(scanner.nextInt(), scanner.nextInt())
                    )
            );
        }
    }
}
