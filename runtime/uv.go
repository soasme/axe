package main

// uv provisioning — entirely offline. The uv release archive is embedded in
// the payload; it is extracted once into the shared cache and reused by every
// axe app pinning the same uv version.

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
)

func uvExeName() string {
	if runtime.GOOS == "windows" {
		return "uv.exe"
	}
	return "uv"
}

// ensureUV returns the path to a uv binary of the pinned version. AXE_UV
// overrides everything (tests, packagers).
func ensureUV(c *config, p *payload) (string, error) {
	if override := os.Getenv("AXE_UV"); override != "" {
		return override, nil
	}

	cache, err := cacheDir()
	if err != nil {
		return "", err
	}
	uvPath := filepath.Join(cache, "uv", c.UVVersion, uvExeName())
	if _, err := os.Stat(uvPath); err == nil {
		return uvPath, nil
	}

	archive, err := p.readAll(c.UVArchive)
	if err != nil {
		return "", err
	}
	binary, err := archiveMember(c.UVArchive, archive, uvExeName())
	if err != nil {
		return "", fmt.Errorf("extracting embedded uv: %w", err)
	}

	if err := os.MkdirAll(filepath.Dir(uvPath), 0o755); err != nil {
		return "", err
	}
	tmp := uvPath + fmt.Sprintf(".tmp-%d", os.Getpid())
	if err := os.WriteFile(tmp, binary, 0o755); err != nil {
		return "", err
	}
	if err := os.Rename(tmp, uvPath); err != nil {
		os.Remove(tmp)
		// Another process may have won the race; that's fine.
		if _, statErr := os.Stat(uvPath); statErr != nil {
			return "", err
		}
	}
	return uvPath, nil
}
