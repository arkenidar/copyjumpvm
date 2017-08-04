package copyjumpvm;

public class CopyInstruction {

    private final int copyFrom;
    private final int copyTo;

    public CopyInstruction(int copyFrom, int copyTo) {
        this.copyFrom = copyFrom;
        this.copyTo = copyTo;
    }

    public void executeInstruction(VirtualMachine vm) {
        vm.setMemory(copyTo, vm.getMemory(copyFrom));
    }

}
