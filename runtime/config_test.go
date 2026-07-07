package main

import (
	"path/filepath"
	"strings"
	"testing"
)

const validConfig = `{
	"name": "cowsay",
	"version": "1.0.0",
	"entrypoint": {"kind": "script", "value": "cowsay"},
	"python_version": "3.12",
	"uv_version": "0.10.6",
	"expose": ["python-path"],
	"fingerprint": "abcdef0123456789",
	"wheel_name": "cowsay-1.0.0-py3-none-any.whl",
	"uv_archive": "uv/uv-aarch64-apple-darwin.tar.gz",
	"python_archive": "python/cpython-3.12.13+20260623-aarch64-apple-darwin-install_only_stripped.tar.gz"
}`

func TestParseConfig(t *testing.T) {
	c, err := parseConfig([]byte(validConfig))
	if err != nil {
		t.Fatal(err)
	}
	if c.Name != "cowsay" || c.Entrypoint.Kind != "script" || c.PythonVersion != "3.12" {
		t.Errorf("unexpected config: %+v", c)
	}
	if !c.exposed("python-path") {
		t.Error("python-path should be exposed")
	}
	if c.exposed("metadata") {
		t.Error("metadata should not be exposed")
	}
}

func TestParseConfigMissingField(t *testing.T) {
	broken := strings.Replace(validConfig, `"fingerprint": "abcdef0123456789",`, "", 1)
	if _, err := parseConfig([]byte(broken)); err == nil {
		t.Fatal("expected error for missing fingerprint")
	}
}

func TestParseConfigBadJSON(t *testing.T) {
	if _, err := parseConfig([]byte("{nope")); err == nil {
		t.Fatal("expected error for invalid JSON")
	}
}

func TestInstallDirUsesFingerprint(t *testing.T) {
	t.Setenv("AXE_DATA_DIR", filepath.Join(t.TempDir(), "data"))
	c, err := parseConfig([]byte(validConfig))
	if err != nil {
		t.Fatal(err)
	}
	dir, err := installDir(c)
	if err != nil {
		t.Fatal(err)
	}
	if filepath.Base(dir) != c.Fingerprint || filepath.Base(filepath.Dir(dir)) != c.Name {
		t.Errorf("install dir %q should end in <name>/<fingerprint>", dir)
	}
}

func TestAppCommand(t *testing.T) {
	c, _ := parseConfig([]byte(validConfig))
	install := "/tmp/fake-install"

	argv, err := appCommand(c, install, []string{"hello"})
	if err != nil {
		t.Fatal(err)
	}
	if filepath.Base(argv[0]) != "cowsay" || argv[len(argv)-1] != "hello" {
		t.Errorf("unexpected script argv: %v", argv)
	}

	c.Entrypoint = entrypoint{Kind: "module", Value: "cowsay"}
	argv, _ = appCommand(c, install, nil)
	if argv[1] != "-I" || argv[2] != "-m" || argv[3] != "cowsay" {
		t.Errorf("unexpected module argv: %v", argv)
	}

	c.Entrypoint = entrypoint{Kind: "spec", Value: "cowsay.cli:run"}
	argv, _ = appCommand(c, install, nil)
	if argv[2] != "-c" || !strings.Contains(argv[3], "from cowsay.cli import run") {
		t.Errorf("unexpected spec argv: %v", argv)
	}

	c.Entrypoint = entrypoint{Kind: "nope", Value: "x"}
	if _, err := appCommand(c, install, nil); err == nil {
		t.Error("expected error for unknown entrypoint kind")
	}
}
