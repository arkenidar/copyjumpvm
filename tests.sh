#!/usr/bin/env bash

echo "-> infinite loop detection test (iloop.cj)"
./run.sh vm_programs/iloop.cj |grep "status"

echo "-> terminating program, simple (tloop.cj)"
./run.sh vm_programs/tloop.cj |grep "status"

echo "-> terminating program, counter, more complex then previous (integer_counter.cj)"
./run.sh vm_programs/integer_counter.cj |grep "status"
