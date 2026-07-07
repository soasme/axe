package main

import (
	"archive/zip"
	"bytes"
	"encoding/binary"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func makeZip(t *testing.T, files map[string][]byte) []byte {
	t.Helper()
	var buf bytes.Buffer
	zw := zip.NewWriter(&buf)
	for name, data := range files {
		w, err := zw.Create(name)
		if err != nil {
			t.Fatal(err)
		}
		if _, err := w.Write(data); err != nil {
			t.Fatal(err)
		}
	}
	if err := zw.Close(); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}

func packBinary(stub, payload []byte) []byte {
	trailer := make([]byte, trailerSize)
	binary.LittleEndian.PutUint64(trailer[0:8], uint64(len(stub)))
	binary.LittleEndian.PutUint64(trailer[8:16], uint64(len(payload)))
	binary.LittleEndian.PutUint32(trailer[16:20], trailerFormatVersion)
	copy(trailer[20:], trailerMagic)
	return append(append(append([]byte{}, stub...), payload...), trailer...)
}

func writeTemp(t *testing.T, data []byte) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "binary")
	if err := os.WriteFile(path, data, 0o755); err != nil {
		t.Fatal(err)
	}
	return path
}

func testPayloadZip(t *testing.T) []byte {
	return makeZip(t, map[string][]byte{
		"config.json":           []byte(`{"name":"demo"}`),
		"wheels/demo-1.0.whl":   []byte("PK demo wheel"),
		"wheels/dep-2.0.whl":    []byte("PK dep wheel"),
		"uv/uv-test.tar.gz":     []byte("uv archive"),
		"python/cpython.tar.gz": []byte("python archive"),
	})
}

func TestPayloadRoundTrip(t *testing.T) {
	stub := []byte("fake ELF bytes")
	p, err := openPayload(writeTemp(t, packBinary(stub, testPayloadZip(t))))
	if err != nil {
		t.Fatal(err)
	}
	config, err := p.configBytes()
	if err != nil {
		t.Fatal(err)
	}
	if string(config) != `{"name":"demo"}` {
		t.Errorf("config = %q", config)
	}
	uv, err := p.readAll("uv/uv-test.tar.gz")
	if err != nil {
		t.Fatal(err)
	}
	if string(uv) != "uv archive" {
		t.Errorf("uv = %q", uv)
	}
	wheels := p.wheelNames()
	want := []string{"wheels/demo-1.0.whl", "wheels/dep-2.0.whl"}
	if !reflect.DeepEqual(wheels, want) {
		t.Errorf("wheels = %v, want %v", wheels, want)
	}
}

func TestMissingEntry(t *testing.T) {
	p, err := openPayload(writeTemp(t, packBinary([]byte("stub"), testPayloadZip(t))))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := p.readAll("python/nope.tar.gz"); err == nil {
		t.Fatal("expected error for missing entry")
	}
}

func TestNoTrailer(t *testing.T) {
	if _, err := openPayload(writeTemp(t, []byte("just a plain binary with no payload appended at all........"))); err == nil {
		t.Fatal("expected error for binary without trailer")
	}
}

func TestTinyFile(t *testing.T) {
	if _, err := openPayload(writeTemp(t, []byte("tiny"))); err == nil {
		t.Fatal("expected error for tiny file")
	}
}

func TestCorruptOffsets(t *testing.T) {
	data := packBinary([]byte("stub"), testPayloadZip(t))
	binary.LittleEndian.PutUint64(data[len(data)-trailerSize+8:], 1<<40)
	if _, err := openPayload(writeTemp(t, data)); err == nil {
		t.Fatal("expected error for corrupt offsets")
	}
}

func TestUnsupportedVersion(t *testing.T) {
	data := packBinary([]byte("stub"), testPayloadZip(t))
	binary.LittleEndian.PutUint32(data[len(data)-trailerSize+16:], 99)
	if _, err := openPayload(writeTemp(t, data)); err == nil {
		t.Fatal("expected error for unsupported format version")
	}
}

func TestNotAZip(t *testing.T) {
	if _, err := openPayload(writeTemp(t, packBinary([]byte("stub"), []byte("not a zip archive")))); err == nil {
		t.Fatal("expected error for non-zip payload")
	}
}
