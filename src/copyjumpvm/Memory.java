package copyjumpvm;

import java.util.BitSet;

public class Memory extends BitSet{

    Memory(int size) {
        super(size);
    }
    
    boolean getPathChooser(){
        return getMemoryValue(0);
    }

    void setPathChooser(boolean booleanValue) {
        setMemoryValue(0, booleanValue);
    }

    boolean getMemoryValue(int index) {
        return get(index);
    }

    void setMemoryValue(int index, boolean booleanValue) {
        set(index, booleanValue);
    }
}
