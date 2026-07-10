package main

import (
	"slices"
	"testing"
)

func TestIsolatedEnv(t *testing.T) {
	env := isolatedEnv([]string{
		"PATH=/usr/bin",
		"PYTHONPATH=/home/user/hacks",
		"PYTHONHOME=/opt/py",
		"pythonstartup=/home/user/startup.py",
		"HOME=/home/user",
	})
	for _, kv := range []string{"PATH=/usr/bin", "HOME=/home/user", "PYTHONNOUSERSITE=1", "PYTHONSAFEPATH=1"} {
		if !slices.Contains(env, kv) {
			t.Errorf("missing %s in %v", kv, env)
		}
	}
	for _, kv := range []string{"PYTHONPATH=/home/user/hacks", "PYTHONHOME=/opt/py", "pythonstartup=/home/user/startup.py"} {
		if slices.Contains(env, kv) {
			t.Errorf("user variable %s survived isolation: %v", kv, env)
		}
	}
}

func TestAppEnvDropsInheritedAXE(t *testing.T) {
	env := appEnv([]string{"AXE=0", "axe=no", "PATH=/usr/bin"})
	if !slices.Contains(env, "AXE=1") {
		t.Errorf("missing AXE=1 in %v", env)
	}
	for _, kv := range []string{"AXE=0", "axe=no"} {
		if slices.Contains(env, kv) {
			t.Errorf("inherited %s survived: %v", kv, env)
		}
	}
}

func TestInstallerEnv(t *testing.T) {
	env := installerEnv([]string{
		"PATH=/usr/bin",
		"UV_INDEX_URL=https://example.com/simple",
		"UV_PYTHON=3.9",
		"PIP_INDEX_URL=https://example.com/simple",
		"PYTHONPATH=/home/user/hacks",
		"VIRTUAL_ENV=/home/user/.venv",
		"CONDA_PREFIX=/opt/conda",
		"HOME=/home/user",
	})
	for _, kv := range []string{"PATH=/usr/bin", "HOME=/home/user", "UV_NO_CONFIG=1", "UV_OFFLINE=1"} {
		if !slices.Contains(env, kv) {
			t.Errorf("missing %s in %v", kv, env)
		}
	}
	for _, kv := range []string{
		"UV_INDEX_URL=https://example.com/simple",
		"UV_PYTHON=3.9",
		"PIP_INDEX_URL=https://example.com/simple",
		"PYTHONPATH=/home/user/hacks",
		"VIRTUAL_ENV=/home/user/.venv",
		"CONDA_PREFIX=/opt/conda",
	} {
		if slices.Contains(env, kv) {
			t.Errorf("user variable %s survived isolation: %v", kv, env)
		}
	}
}
