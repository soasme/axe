//go:build !windows

package main

import (
	"fmt"
	"os"
	"syscall"
)

func execProcess(argv, env []string) error {
	if _, err := os.Stat(argv[0]); err != nil {
		return fmt.Errorf("entrypoint %s does not exist; the installation may be corrupt (try `self restore`)", argv[0])
	}
	return syscall.Exec(argv[0], argv, env)
}
