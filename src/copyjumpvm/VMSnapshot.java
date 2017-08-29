package copyjumpvm;

public class VMSnapshot {

    private int currentInstruction;
    private Memory memory;

    VMSnapshot(int currentInstruction, Memory memory){
        this.currentInstruction = currentInstruction;
        this.memory = memory;
    }

    @Override
    public boolean equals(Object o) {

        if (o == this) return true;
        if (!(o instanceof VMSnapshot)) {
            return false;
        }

        VMSnapshot vms = (VMSnapshot) o;

        //System.out.print("vms.equals() used (mem:"+memory+", mem2:"+vms.memory+")");
        //System.out.println("(ci:"+currentInstruction+", ci2:"+vms.currentInstruction+")");

        return
                vms.currentInstruction == currentInstruction &&
                vms.memory.equals(memory);

    }

    @Override
    public String toString(){
        return currentInstruction+":"+String.valueOf(memory);
    }
}
