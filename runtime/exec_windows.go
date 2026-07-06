//go:build windows

package main

import (
	"fmt"
	"os"
	"os/exec"
	"os/signal"
)

func execProcess(argv, env []string) error {
	if _, err := os.Stat(argv[0]); err != nil {
		return fmt.Errorf("entrypoint %s does not exist; the installation may be corrupt (try `self restore`)", argv[0])
	}
	cmd := exec.Command(argv[0], argv[1:]...)
	cmd.Env = env
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	// Let the child own Ctrl+C; the wrapper just waits and forwards the code.
	signal.Ignore(os.Interrupt)
	if err := cmd.Run(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		return err
	}
	os.Exit(0)
	return nil
}
