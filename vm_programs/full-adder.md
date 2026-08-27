full-adder:
-----------

* inputs:
    - A
    - B
    - CIN
    
* outputs:
    - COUT
    - S

```python
if A == 0:
    COUT = and(B, CIN)
    S = xor(B, CIN)
    
if A == 1:
    COUT = or(B, CIN)
    S = xnor(B, CIN)
```
