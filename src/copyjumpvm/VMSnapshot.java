package copyjumpvm;

public class VMSnapshot {
    private Memory memory;
    private int currentInstruction;
    VMSnapshot(Memory memory, int currentInstruction){
        this.memory = memory;
        this.currentInstruction = currentInstruction;
    }

    @Override
    public boolean equals(Object o) {

        if (o == this) return true;
        if (!(o instanceof VMSnapshot)) {
            return false;
        }

        VMSnapshot vms = (VMSnapshot) o;

        return vms.memory.equals(memory) &&
                vms.currentInstruction == currentInstruction;
    }
}
