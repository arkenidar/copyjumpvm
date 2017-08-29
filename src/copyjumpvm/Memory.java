package copyjumpvm;

import java.util.BitSet;

public class Memory {
    private BitSet values;

    Memory(int size) {
        values = new BitSet(size);
    }

    Memory(BitSet values) {
        this.values = values;
    }

    BitSet getValues(){
        return values;
    }
    
    boolean getPathChooser(){
        return getMemoryValue(0);
    }

    void setPathChooser(boolean booleanValue) {
        setMemoryValue(0, booleanValue);
    }

    boolean getMemoryValue(int index) {
        return values.get(index);
    }

    void setMemoryValue(int index, boolean booleanValue) {
        values.set(index, booleanValue);
    }

    @Override
    public boolean equals(Object o) {
        //System.out.println("memory.equals() used");

        if (o == this) return true;
        if (!(o instanceof Memory)) {
            return false;
        }

        Memory memory = (Memory) o;

        return memory.values.equals(values);
    }

    @Override
    public int hashCode() {
        //System.out.println("memory.hashCode() used");
        return values.hashCode();
    }

    @Override
    public String toString(){
        return String.valueOf(values);
    }

    @Override
    public Object clone(){
        return new Memory((BitSet) values.clone());
    }
}
