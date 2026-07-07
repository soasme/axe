package main

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

func makeTarGz(t *testing.T, entries []tar.Header, contents map[string]string) []byte {
	t.Helper()
	var buf bytes.Buffer
	gz := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gz)
	for _, hdr := range entries {
		h := hdr
		if body, ok := contents[h.Name]; ok {
			h.Size = int64(len(body))
		}
		if err := tw.WriteHeader(&h); err != nil {
			t.Fatal(err)
		}
		if body, ok := contents[h.Name]; ok {
			if _, err := tw.Write([]byte(body)); err != nil {
				t.Fatal(err)
			}
		}
	}
	if err := tw.Close(); err != nil {
		t.Fatal(err)
	}
	if err := gz.Close(); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}

func TestUntarGzStripsPrefixAndPreservesLayout(t *testing.T) {
	data := makeTarGz(t,
		[]tar.Header{
			{Name: "python/", Typeflag: tar.TypeDir, Mode: 0o755},
			{Name: "python/bin/", Typeflag: tar.TypeDir, Mode: 0o755},
			{Name: "python/bin/python3.12", Typeflag: tar.TypeReg, Mode: 0o755},
			{Name: "python/bin/python3", Typeflag: tar.TypeSymlink, Linkname: "python3.12", Mode: 0o777},
			{Name: "python/lib/data.txt", Typeflag: tar.TypeReg, Mode: 0o644},
		},
		map[string]string{
			"python/bin/python3.12": "#!fake interpreter",
			"python/lib/data.txt":   "hello",
		},
	)
	dest := t.TempDir()
	if err := untarGz(bytes.NewReader(data), dest, true); err != nil {
		t.Fatal(err)
	}

	body, err := os.ReadFile(filepath.Join(dest, "bin", "python3.12"))
	if err != nil {
		t.Fatal(err)
	}
	if string(body) != "#!fake interpreter" {
		t.Errorf("unexpected content: %q", body)
	}
	if runtime.GOOS != "windows" {
		info, err := os.Stat(filepath.Join(dest, "bin", "python3.12"))
		if err != nil {
			t.Fatal(err)
		}
		if info.Mode().Perm()&0o111 == 0 {
			t.Error("exec bit not preserved")
		}
		// The symlink resolves through to the real interpreter.
		viaLink, err := os.ReadFile(filepath.Join(dest, "bin", "python3"))
		if err != nil {
			t.Fatal(err)
		}
		if string(viaLink) != "#!fake interpreter" {
			t.Errorf("symlink content: %q", viaLink)
		}
	}
}

func TestUntarGzRejectsTraversal(t *testing.T) {
	data := makeTarGz(t,
		[]tar.Header{{Name: "python/../../evil.txt", Typeflag: tar.TypeReg, Mode: 0o644}},
		map[string]string{"python/../../evil.txt": "boom"},
	)
	if err := untarGz(bytes.NewReader(data), t.TempDir(), true); err == nil {
		t.Fatal("expected traversal rejection")
	}
}

func TestArchiveMemberTarGz(t *testing.T) {
	data := makeTarGz(t,
		[]tar.Header{{Name: "uv-x86_64/uv", Typeflag: tar.TypeReg, Mode: 0o755}},
		map[string]string{"uv-x86_64/uv": "uv binary bytes"},
	)
	got, err := archiveMember("uv-test.tar.gz", data, "uv")
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != "uv binary bytes" {
		t.Errorf("member = %q", got)
	}
	if _, err := archiveMember("uv-test.tar.gz", data, "missing"); err == nil {
		t.Fatal("expected error for missing member")
	}
}

func TestArchiveMemberZip(t *testing.T) {
	data := makeZip(t, map[string][]byte{"uv.exe": []byte("uv.exe bytes")})
	got, err := archiveMember("uv-test.zip", data, "uv.exe")
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != "uv.exe bytes" {
		t.Errorf("member = %q", got)
	}
}
