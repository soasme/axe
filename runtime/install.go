package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

// isInstalled is the fast path checked on every run.
func isInstalled(install string) bool {
	_, err := os.Stat(install)
	return err == nil
}

// ensureInstalled bootstraps the environment on first run: uv -> venv with
// the pinned Python -> install the embedded wheel. The bootstrap happens in a
// temp directory renamed into place, so a partial install is never observed.
func ensureInstalled(c *config, p *payload) (string, error) {
	install, err := installDir(c)
	if err != nil {
		return "", err
	}
	if isInstalled(install) {
		debugf("already installed at %s", install)
		return install, nil
	}

	if err := os.MkdirAll(filepath.Dir(install), 0o755); err != nil {
		return "", err
	}
	unlock, err := acquireLock(install + ".lock")
	if err != nil {
		return "", err
	}
	defer unlock()
	// Another process may have finished the bootstrap while we waited.
	if isInstalled(install) {
		return install, nil
	}

	statusf("setting up %s %s (first run)...", c.Name, c.Version)
	uv, err := ensureUV(c.UVVersion)
	if err != nil {
		return "", err
	}

	tmp := fmt.Sprintf("%s.tmp-%d", install, os.Getpid())
	if err := os.RemoveAll(tmp); err != nil {
		return "", err
	}
	defer os.RemoveAll(tmp)

	if err := bootstrap(c, p, uv, tmp); err != nil {
		return "", err
	}

	if err := os.Rename(tmp, install); err != nil {
		if isInstalled(install) { // lost a race; the other install is fine
			return install, nil
		}
		return "", err
	}
	statusf("done.")
	return install, nil
}

func bootstrap(c *config, p *payload, uv, dir string) error {
	// --relocatable: the venv is created in a temp dir and renamed into place
	// atomically, so nothing inside it may reference the temp path.
	if err := runUV(uv, "venv", "--relocatable", "--python", c.PythonVersion, venvDir(dir)); err != nil {
		return fmt.Errorf("creating virtual environment: %w", err)
	}

	wheel, err := p.wheelBytes()
	if err != nil {
		return fmt.Errorf("reading embedded wheel: %w", err)
	}
	wheelPath := filepath.Join(dir, c.WheelName)
	if err := os.WriteFile(wheelPath, wheel, 0o644); err != nil {
		return err
	}
	defer os.Remove(wheelPath)

	if err := runUV(uv, "pip", "install", "--python", venvPython(dir), wheelPath); err != nil {
		return fmt.Errorf("installing application: %w", err)
	}
	return nil
}

// runUV runs uv with user configuration disabled so behavior is identical on
// every machine (the same guarantee pyapp makes for pip).
func runUV(uv string, args ...string) error {
	if os.Getenv("AXE_DEBUG") == "" {
		args = append(args, "--quiet")
	}
	debugf("running: %s %v", uv, args)
	cmd := exec.Command(uv, args...)
	cmd.Env = append(os.Environ(), "UV_NO_CONFIG=1")
	cmd.Stdout = os.Stderr
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// acquireLock guards the bootstrap against concurrent first runs using an
// exclusively-created lock file. Locks older than staleLockAge are assumed to
// be left over from a crashed process.
const (
	lockTimeout  = 10 * time.Minute
	staleLockAge = 15 * time.Minute
)

func acquireLock(path string) (func(), error) {
	deadline := time.Now().Add(lockTimeout)
	for {
		f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o644)
		if err == nil {
			f.Close()
			return func() { os.Remove(path) }, nil
		}
		if !errors.Is(err, fs.ErrExist) {
			return nil, err
		}
		if info, statErr := os.Stat(path); statErr == nil && time.Since(info.ModTime()) > staleLockAge {
			debugf("removing stale lock %s", path)
			os.Remove(path)
			continue
		}
		if time.Now().After(deadline) {
			return nil, fmt.Errorf("timed out waiting for another installation to finish (remove %s if none is running)", path)
		}
		debugf("waiting for lock %s", path)
		time.Sleep(200 * time.Millisecond)
	}
}
