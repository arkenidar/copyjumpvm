
syntax for comments:
-------------------

* # for a comment
* #begin: for a begin-comment
* #end: for a end-comment

syntax for statements (with parameters):
---------------------------------------

* Move {copy_to_memory_address} {copy_from_memory_address}
* Jump {label_to_jump_to}
* Jump {condition_at_memory_address} {label_to_jump_to_if_condition_is_1}
* Jump {condition_at_memory_address} {label_to_jump_to_if_condition_is_0} {label_to_jump_to_if_condition_is_1}
* Label {jump_destination_label}

possible further syntax (todo):
-------------------------------

* . for a memory-location label
* - for a program-line label
