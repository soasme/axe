package main

import (
	"fmt"
	"os"
	"strings"
)

// appCommand resolves the configured entrypoint to an argv within the
// installed environment.
func appCommand(c *config, install string, args []string) ([]string, error) {
	switch c.Entrypoint.Kind {
	case "script":
		return append([]string{venvScript(install, c.Entrypoint.Value)}, args...), nil
	case "module":
		return append([]string{venvPython(install), "-I", "-m", c.Entrypoint.Value}, args...), nil
	case "spec":
		mod, fn, ok := strings.Cut(c.Entrypoint.Value, ":")
		if !ok {
			return nil, fmt.Errorf("invalid entrypoint spec %q", c.Entrypoint.Value)
		}
		code := fmt.Sprintf("import sys;from %s import %s;sys.exit(%s())", mod, fn, fn)
		return append([]string{venvPython(install), "-I", "-c", code}, args...), nil
	}
	return nil, fmt.Errorf("unknown entrypoint kind %q", c.Entrypoint.Kind)
}

// executeApp hands control to the application: process replacement on
// non-Windows (see exec_unix.go), child process with exit-code forwarding on
// Windows (see exec_windows.go). AXE=1 lets apps detect this install mode.
func executeApp(c *config, install string, args []string) error {
	argv, err := appCommand(c, install, args)
	if err != nil {
		return err
	}
	env := append(os.Environ(), "AXE=1")
	debugf("executing: %v", argv)
	return execProcess(argv, env)
}
