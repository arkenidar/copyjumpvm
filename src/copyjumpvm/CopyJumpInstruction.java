package copyjumpvm;

public class CopyJumpInstruction {

    private final CopyInstruction copy;
    private final JumpInstruction jump;

    CopyJumpInstruction(CopyInstruction copy, JumpInstruction jump){
        this.copy = copy;
        this.jump = jump;
    }

    /**
     * Executes an instruction.
     */
    public void executeInstruction(VirtualMachine vm){
        copy.executeInstruction(vm);
        jump.executeInstruction(vm);
    }

}
