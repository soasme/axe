package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// markerName flags a completed installation. The bootstrap happens directly
// in the final directory (the venv bakes absolute paths to the embedded
// Python, so it cannot be built elsewhere and renamed); the marker is written
// last, and a directory without it is treated as crash residue and rebuilt.
const markerName = ".axe-installed"

// isInstalled is the fast path checked on every run.
func isInstalled(install string) bool {
	_, err := os.Stat(filepath.Join(install, markerName))
	return err == nil
}

// ensureInstalled bootstraps the environment on first run — with zero
// network access: uv, CPython, and every wheel come from the embedded
// payload.
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

	statusf("[axe] bootstrapping %s %s...", c.Name, c.Version)
	if err := bootstrap(c, p, install); err != nil {
		return "", err
	}
	return install, nil
}

func bootstrap(c *config, p *payload, install string) error {
	// Clear crash residue from a previous interrupted bootstrap.
	if err := os.RemoveAll(install); err != nil {
		return err
	}
	if err := os.MkdirAll(install, 0o755); err != nil {
		return err
	}

	uv, err := ensureUV(c, p)
	if err != nil {
		return err
	}

	pythonArchive, err := p.open(c.PythonArchive)
	if err != nil {
		return err
	}
	defer pythonArchive.Close()
	if err := untarGz(pythonArchive, filepath.Join(install, "python"), true); err != nil {
		return fmt.Errorf("extracting embedded Python: %w", err)
	}

	wheelsDir := filepath.Join(install, "wheels")
	if err := extractWheels(p, wheelsDir); err != nil {
		return fmt.Errorf("extracting embedded wheels: %w", err)
	}
	defer os.RemoveAll(wheelsDir)

	if err := runUV(uv, "venv", "--python", pbsPython(install), venvDir(install)); err != nil {
		return fmt.Errorf("creating virtual environment: %w", err)
	}
	if err := runUV(uv,
		"pip", "install",
		"--python", venvPython(install),
		"--offline", "--no-index",
		"--find-links", wheelsDir,
		filepath.Join(wheelsDir, c.WheelName),
	); err != nil {
		return fmt.Errorf("installing application: %w", err)
	}

	return os.WriteFile(filepath.Join(install, markerName), []byte(c.Fingerprint+"\n"), 0o644)
}

func extractWheels(p *payload, dest string) error {
	if err := os.MkdirAll(dest, 0o755); err != nil {
		return err
	}
	for _, name := range p.wheelNames() {
		data, err := p.readAll(name)
		if err != nil {
			return err
		}
		if err := os.WriteFile(filepath.Join(dest, strings.TrimPrefix(name, "wheels/")), data, 0o644); err != nil {
			return err
		}
	}
	return nil
}

// installerEnv is the uv analogue of `pip --isolated`: every variable that
// could steer uv or the embedded Python is dropped, so the bootstrap behaves
// identically on every machine. UV_OFFLINE guarantees uv can never reach for
// the network, even for operations where we don't pass --offline explicitly.
func installerEnv(env []string) []string {
	out := make([]string, 0, len(env)+2)
	for _, kv := range env {
		key, _, _ := strings.Cut(kv, "=")
		upper := strings.ToUpper(key)
		if strings.HasPrefix(upper, "UV_") || strings.HasPrefix(upper, "PIP_") ||
			strings.HasPrefix(upper, "PYTHON") ||
			upper == "VIRTUAL_ENV" || upper == "CONDA_PREFIX" {
			continue
		}
		out = append(out, kv)
	}
	return append(out, "UV_NO_CONFIG=1", "UV_OFFLINE=1")
}

// runUV runs uv with user configuration and environment influence disabled
// so behavior is identical on every machine.
func runUV(uv string, args ...string) error {
	if os.Getenv("AXE_DEBUG") == "" {
		args = append(args, "--quiet")
	}
	debugf("running: %s %v", uv, args)
	cmd := exec.Command(uv, args...)
	cmd.Env = installerEnv(os.Environ())
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
