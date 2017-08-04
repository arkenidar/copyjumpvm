package copyjumpvm;

public class JumpInstruction {

    private final int caseTrue;
    private final int caseFalse;

    public JumpInstruction(int caseTrue, int caseZero) {
        this.caseTrue = caseTrue;
        this.caseFalse = caseZero;
    }

    public void executeInstruction(VirtualMachine vm) {
        vm.relativeJump(vm.getPathChooser()?caseTrue:caseFalse);
    }

}
