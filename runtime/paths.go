package main

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
)

// dataDir is where per-app installations live. AXE_DATA_DIR overrides it
// (used by tests and power users).
func dataDir() (string, error) {
	if dir := os.Getenv("AXE_DATA_DIR"); dir != "" {
		return dir, nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("cannot determine home directory: %w", err)
	}
	switch runtime.GOOS {
	case "darwin":
		return filepath.Join(home, "Library", "Application Support", "axe"), nil
	case "windows":
		if dir := os.Getenv("LOCALAPPDATA"); dir != "" {
			return filepath.Join(dir, "axe"), nil
		}
		return filepath.Join(home, "AppData", "Local", "axe"), nil
	default:
		if dir := os.Getenv("XDG_DATA_HOME"); dir != "" {
			return filepath.Join(dir, "axe"), nil
		}
		return filepath.Join(home, ".local", "share", "axe"), nil
	}
}

// cacheDir holds assets shared across apps (the uv binaries).
// AXE_CACHE_DIR overrides it.
func cacheDir() (string, error) {
	if dir := os.Getenv("AXE_CACHE_DIR"); dir != "" {
		return dir, nil
	}
	base, err := os.UserCacheDir()
	if err != nil {
		return "", fmt.Errorf("cannot determine cache directory: %w", err)
	}
	return filepath.Join(base, "axe"), nil
}

func installDir(c *config) (string, error) {
	base, err := dataDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(base, c.Name, c.Fingerprint), nil
}

func venvDir(install string) string {
	return filepath.Join(install, "venv")
}

func venvPython(install string) string {
	if runtime.GOOS == "windows" {
		return filepath.Join(venvDir(install), "Scripts", "python.exe")
	}
	return filepath.Join(venvDir(install), "bin", "python")
}

func venvScript(install, name string) string {
	if runtime.GOOS == "windows" {
		return filepath.Join(venvDir(install), "Scripts", name+".exe")
	}
	return filepath.Join(venvDir(install), "bin", name)
}
