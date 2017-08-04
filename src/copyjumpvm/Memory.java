package copyjumpvm;

public class Memory {
    private boolean[] values;

    Memory(int size) {
        values = new boolean[size];
    }
    
    boolean getPathChooser(){
        return values[0];
    }

    void setPathChooser(boolean booleanValue) {
        values[0] = booleanValue;
    }

    boolean getMemoryValue(int index) {
        return values[index];
    }

    void setMemoryValue(int index, boolean booleanValue) {
        values[index] = booleanValue;
    }
}
