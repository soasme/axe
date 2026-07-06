package main

import (
	"bytes"
	"encoding/binary"
	"os"
	"path/filepath"
	"testing"
)

func packBinary(stub, wheel, config []byte) []byte {
	var buf bytes.Buffer
	buf.Write(stub)
	buf.Write(wheel)
	buf.Write(config)
	trailer := make([]byte, trailerSize)
	binary.LittleEndian.PutUint64(trailer[0:8], uint64(len(stub)))
	binary.LittleEndian.PutUint64(trailer[8:16], uint64(len(wheel)))
	binary.LittleEndian.PutUint64(trailer[16:24], uint64(len(stub)+len(wheel)))
	binary.LittleEndian.PutUint64(trailer[24:32], uint64(len(config)))
	binary.LittleEndian.PutUint32(trailer[32:36], trailerFormatVersion)
	copy(trailer[36:], trailerMagic)
	buf.Write(trailer)
	return buf.Bytes()
}

func writeTemp(t *testing.T, data []byte) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "binary")
	if err := os.WriteFile(path, data, 0o755); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestPayloadRoundTrip(t *testing.T) {
	stub := []byte("fake ELF bytes")
	wheel := []byte("PK\x03\x04 wheel contents")
	config := []byte(`{"name":"demo"}`)

	p, err := openPayload(writeTemp(t, packBinary(stub, wheel, config)))
	if err != nil {
		t.Fatal(err)
	}
	gotConfig, err := p.configBytes()
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(gotConfig, config) {
		t.Errorf("config = %q, want %q", gotConfig, config)
	}
	gotWheel, err := p.wheelBytes()
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(gotWheel, wheel) {
		t.Errorf("wheel = %q, want %q", gotWheel, wheel)
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
	data := packBinary([]byte("stub"), []byte("wheel"), []byte("config"))
	// Point the wheel section past EOF.
	binary.LittleEndian.PutUint64(data[len(data)-trailerSize+8:], 1<<40)
	if _, err := openPayload(writeTemp(t, data)); err == nil {
		t.Fatal("expected error for corrupt offsets")
	}
}

func TestUnsupportedVersion(t *testing.T) {
	data := packBinary([]byte("stub"), []byte("wheel"), []byte("config"))
	binary.LittleEndian.PutUint32(data[len(data)-trailerSize+32:], 99)
	if _, err := openPayload(writeTemp(t, data)); err == nil {
		t.Fatal("expected error for unsupported format version")
	}
}
