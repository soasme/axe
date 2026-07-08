package main

import (
	"fmt"
	"os"
	"slices"
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

// isolatedEnv replicates `python -I` for entrypoints the interpreter flag
// cannot reach (console scripts run the venv python via their shebang):
// every PYTHON* variable is dropped (-E), then user site-packages and
// script-dir sys.path prepending are disabled (-s, -P). Module and spec
// entrypoints pass -I too, which subsumes all of this.
func isolatedEnv(env []string) []string {
	out := make([]string, 0, len(env)+2)
	for _, kv := range env {
		key, _, _ := strings.Cut(kv, "=")
		if strings.HasPrefix(strings.ToUpper(key), "PYTHON") {
			continue
		}
		out = append(out, kv)
	}
	return append(out, "PYTHONNOUSERSITE=1", "PYTHONSAFEPATH=1")
}

// appEnv is the environment handed to the application: Python isolation
// plus the canonical AXE=1 marker. Any inherited AXE value is dropped first —
// duplicate entries would let a user-set AXE=0 win on some platforms.
func appEnv(env []string) []string {
	out := slices.DeleteFunc(isolatedEnv(env), func(kv string) bool {
		key, _, _ := strings.Cut(kv, "=")
		return strings.EqualFold(key, "AXE")
	})
	return append(out, "AXE=1")
}

// executeApp hands control to the application: process replacement on
// non-Windows (see exec_unix.go), child process with exit-code forwarding on
// Windows (see exec_windows.go). AXE=1 lets apps detect this install mode.
func executeApp(c *config, install string, args []string) error {
	argv, err := appCommand(c, install, args)
	if err != nil {
		return err
	}
	env := appEnv(os.Environ())
	debugf("executing: %v", argv)
	return execProcess(argv, env)
}
