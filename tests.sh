#!/usr/bin/env bash

./run.sh iloop.cj |grep "status"
./run.sh tloop.cj |grep "status"
./run.sh integer_counter.cj |grep "status"
