#!/bin/sh
# Thanks to http://www.sergiy.ca/how-to-compile-and-launch-java-code-from-command-line/

NAME=copyjumpvm
COM="$NAME.Main"
SRCS=src
BIN=bin

build() {
	echo "building..."
	mkdir -p "$BIN"
	/usr/bin/javac -d "$BIN" -sourcepath "$SRCS" "$SRCS/$NAME/"*.java
}

clean() {
	echo "cleaning..."
	rm -fr "$SRCS/$NAME/*.class" "$BIN"
}

run() {
	echo "running..."
	/usr/bin/java -cp "$BIN" "$COM" $@
}

main() {
	case $1 in
	build|clean|run)
		cmd=$1
		shift
		$cmd $@;;
	*) echo "Usage: $0 [build|clean|run]"; exit 1;;
	esac
}

main "$@"
