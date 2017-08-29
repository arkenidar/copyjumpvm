package copyjumpvm;

import java.util.*;

public class VirtualMachine {
    private int currentInstruction;
    private final Memory memory;
    private final Instructions instructions;

    VirtualMachine(Instructions instructions, Memory memory) {
        this.instructions = instructions;
        this.memory = memory;
        this.bitPrinter = new BitPrinter();
        snapshotSet = new LinkedHashSet<VMSnapshot>();
    }

    void relativeJump(Integer offset) {
        currentInstruction += offset;
    }

    boolean getPathChooser() {
        return memory.getPathChooser();
    }

    private BitPrinter bitPrinter;
    void setMemory(int index, boolean booleanValue){
        switch(index){
            case 0: break;
            case 1: break;
            case 2:
                memory.setPathChooser(booleanValue);
                break;
            case 3:
                System.out.println("out: "+(booleanValue?"1":"0"));
                bitPrinter.printBit(booleanValue?1:0);
                break;
            default:
                memory.setMemoryValue(index, booleanValue);
                break;
        }
    }
    
    boolean getMemory(int index){
        boolean value;
        switch(index){
            case 0:
                value = false;
                break;
            case 1:
                value = true;
                break;
            case 2:
                value = memory.getPathChooser();
                break;
            case 3:
                int intValue = -1;
                do{
                    System.out.print("in: ");
                    Scanner scanner = new Scanner(System.in);
                    try{
                        intValue = scanner.nextInt();
                        if(intValue!=0 && intValue!=1)
                            System.out.println("(not 0 or 1, input ignored, retrying)");
                    }catch(Exception e){
                        System.out.println("(not 0 or 1, input ignored, exiting)");
                        System.exit(0);
                    }
                }while(intValue!=0 && intValue!=1);
                value = intValue==1;
                break;
            default:
                value = memory.getMemoryValue(index);
                break;
        }
        return value;
    }
    
    void run() {
        while(true){
            try{
                CopyJumpInstruction instruction = instructions.instructions.get(currentInstruction);

                boolean sameAlreadyThere = save(memory, currentInstruction);
                if (sameAlreadyThere) {
                    System.out.println("status: loop detected");
                    //break; // you can also continue, don't break
                }

                instruction.executeInstruction(this);
            }catch(IndexOutOfBoundsException e){
                System.out.println("status: terminated");
                break;
            }
        }
    }

    private LinkedHashSet<VMSnapshot> snapshotSet;
    private Boolean save(Memory memory, int currentInstruction) {
        VMSnapshot snapshot = new VMSnapshot(currentInstruction, (Memory) memory.clone());
        System.out.println("saving: "+snapshot);
        boolean alreadyContained = !snapshotSet.add(snapshot);
        //System.out.println(snapshotSet);
        return alreadyContained;
    }

}
