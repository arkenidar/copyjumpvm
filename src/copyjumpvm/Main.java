package copyjumpvm;

import java.io.FileNotFoundException;

/**
 * @author Dario Cangialosi
 * Simple Virtual Machine (VM) based on a matrix of integers.
 */
public class Main {
    
    public static void main(String[] args) throws FileNotFoundException {
        try{
            Instructions instructions = new Instructions("not_gate.cj");
            VirtualMachine vm;
            vm = new VirtualMachine(instructions, new Memory(1024));
            vm.run();    
        }catch(FileNotFoundException e){
            System.out.println("Working Directory = " +
              System.getProperty("user.dir"));
        }
    }
    
}
