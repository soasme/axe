package main

import (
	"fmt"
	"os"
	"path/filepath"
	"slices"
)

// runSelf handles the reserved `self` management command group. Mirrors
// pyapp: remove/restore/update always exist; the rest must be exposed at
// build time.
func runSelf(c *config, p *payload, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("usage: self <remove|restore|update%s>", exposedUsage(c))
	}
	command, rest := args[0], args[1:]

	hidden := slices.Contains([]string{"python", "python-path", "cache", "metadata"}, command)
	if hidden && !c.exposed(command) {
		return fmt.Errorf("unknown self command %q", command)
	}

	install, err := installDir(c)
	if err != nil {
		return err
	}

	switch command {
	case "remove":
		return removeInstall(c, install)
	case "restore", "update":
		if err := removeInstall(c, install); err != nil {
			return err
		}
		_, err := ensureInstalled(c, p)
		return err
	case "python":
		if _, err := ensureInstalled(c, p); err != nil {
			return err
		}
		return execProcess(append([]string{venvPython(install)}, rest...), os.Environ())
	case "python-path":
		if _, err := ensureInstalled(c, p); err != nil {
			return err
		}
		fmt.Println(venvPython(install))
		return nil
	case "cache":
		return runCache(c, rest)
	case "metadata":
		fmt.Printf("name: %s\nversion: %s\npython: %s\nuv: %s\ninstall: %s\n",
			c.Name, c.Version, c.PythonVersion, c.UVVersion, install)
		return nil
	}
	return fmt.Errorf("unknown self command %q", command)
}

func exposedUsage(c *config) string {
	usage := ""
	for _, cmd := range c.Expose {
		usage += "|" + cmd
	}
	return usage
}

func removeInstall(c *config, install string) error {
	if !isInstalled(install) {
		statusf("%s is not installed", c.Name)
		return nil
	}
	if err := os.RemoveAll(install); err != nil {
		return err
	}
	statusf("removed %s", install)
	return nil
}

// runCache shows or removes the shared uv cache: `self cache [uv] [-r]`.
func runCache(c *config, args []string) error {
	remove := false
	for _, arg := range args {
		switch arg {
		case "-r", "--remove":
			remove = true
		case "uv":
			// the only cached asset kind in v1
		default:
			return fmt.Errorf("usage: self cache [uv] [-r|--remove]")
		}
	}
	cache, err := cacheDir()
	if err != nil {
		return err
	}
	uvCache := filepath.Join(cache, "uv")
	if remove {
		if err := os.RemoveAll(uvCache); err != nil {
			return err
		}
		statusf("removed %s", uvCache)
		return nil
	}
	fmt.Println(uvCache)
	return nil
}
