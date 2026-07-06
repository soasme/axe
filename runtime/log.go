package main

import (
	"fmt"
	"os"
)

// statusf reports bootstrap progress to stderr so it never pollutes the
// app's stdout.
func statusf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
}

func debugf(format string, args ...any) {
	if os.Getenv("AXE_DEBUG") != "" {
		fmt.Fprintf(os.Stderr, "[axe] "+format+"\n", args...)
	}
}

func fatalf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "error: "+format+"\n", args...)
	os.Exit(1)
}
