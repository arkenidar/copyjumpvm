package copyjumpvm;

import java.io.FileNotFoundException;

/**
 * @author Dario Cangialosi
 * Simple Virtual Machine (VM) based on a matrix of integers.
 */
public class Main {
    
    public static void main(String[] args) throws FileNotFoundException {
        try{
            Instructions instructions = new Instructions("iloop.cj");
            VirtualMachine vm;
            vm = new VirtualMachine(instructions, new Memory(1024));
            vm.run();    
        }catch(FileNotFoundException e){
            System.out.println("FileNotFoundException ... Working Directory = " +
              System.getProperty("user.dir"));
        }
    }
    
}
