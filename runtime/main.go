// axe runtime stub: prepended to every binary built by `axe build`.
//
// First run: bootstrap uv -> Python -> app into a cached environment.
// Every other run: a single existence check, then hand off to the app.
package main

import "os"

func main() {
	exe, err := os.Executable()
	if err != nil {
		fatalf("cannot locate own executable: %v", err)
	}
	p, err := openPayload(exe)
	if err != nil {
		fatalf("%v", err)
	}
	configData, err := p.configBytes()
	if err != nil {
		fatalf("reading embedded config: %v", err)
	}
	c, err := parseConfig(configData)
	if err != nil {
		fatalf("%v", err)
	}

	args := os.Args[1:]
	if len(args) > 0 && args[0] == "self" {
		if err := runSelf(c, p, args[1:]); err != nil {
			fatalf("%v", err)
		}
		return
	}

	install, err := ensureInstalled(c, p)
	if err != nil {
		fatalf("%v", err)
	}
	if err := executeApp(c, install, args); err != nil {
		fatalf("%v", err)
	}
}
