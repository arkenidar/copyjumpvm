package copyjumpvm;

import java.io.FileNotFoundException;

/**
 * @author Dario Cangialosi
 * Simple Virtual Machine (VM) based on a matrix of integers.
 */
public class Main {
    public static void main(String[] args) throws FileNotFoundException {
        /*
        $ ./run.sh integer_counter.cj |grep "status"
        status: vm starts
        status: terminated
        $ ./run.sh iloop.cj |grep "status"
        status: vm starts
        status: loop detected
        $ ./run.sh tloop.cj |grep "status"
        status: vm starts
        status: terminated
        */

        try{
            Instructions instructions = new Instructions(args[0]); //args[0], tloop, iloop, integer_counter
            VirtualMachine vm;
            vm = new VirtualMachine(instructions, new Memory(1024));
            System.out.println("status: vm starts");
            vm.run();    
        }catch(FileNotFoundException e){
            System.out.println("FileNotFoundException ... Working Directory = " +
              System.getProperty("user.dir"));
        }catch (ArrayIndexOutOfBoundsException e){
            System.out.println("Pass a *.cj file as the first parameter of this program.");
        }
    }
    
}
