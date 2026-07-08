package main

// Payload trailer parsing. Must mirror src/axe/trailer.py exactly:
//
//	[stub][payload zip][u64 payload off][u64 payload len][u32 version]["AXEBIN01"]
//
// The payload zip holds config.json, wheels/, uv/<archive>, python/<archive> —
// everything needed to bootstrap with zero network access.

import (
	"archive/zip"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"os"
	"slices"
	"strings"
)

const (
	trailerMagic         = "AXEBIN01"
	trailerSize          = 8 + 8 + 4 + 8
	trailerFormatVersion = 2
)

var errNoTrailer = errors.New("no axe payload found in executable (was this binary built with `axe build`?)")

// payload gives access to the zip archive appended to the executable. The
// underlying file stays open for the process lifetime.
type payload struct {
	zip *zip.Reader
}

func openPayload(exePath string) (*payload, error) {
	f, err := os.Open(exePath)
	if err != nil {
		return nil, fmt.Errorf("cannot open own executable: %w", err)
	}
	info, err := f.Stat()
	if err != nil {
		return nil, err
	}
	if info.Size() < trailerSize {
		return nil, errNoTrailer
	}
	buf := make([]byte, trailerSize)
	if _, err := f.ReadAt(buf, info.Size()-trailerSize); err != nil {
		return nil, err
	}
	if string(buf[20:]) != trailerMagic {
		return nil, errNoTrailer
	}
	if version := binary.LittleEndian.Uint32(buf[16:20]); version != trailerFormatVersion {
		return nil, fmt.Errorf("unsupported payload format version %d (runtime supports %d)", version, trailerFormatVersion)
	}
	offset := binary.LittleEndian.Uint64(buf[0:8])
	length := binary.LittleEndian.Uint64(buf[8:16])
	if offset+length > uint64(info.Size())-trailerSize {
		return nil, errors.New("corrupt trailer: payload extends past end of file")
	}
	zr, err := zip.NewReader(io.NewSectionReader(f, int64(offset), int64(length)), int64(length))
	if err != nil {
		return nil, fmt.Errorf("corrupt payload archive: %w", err)
	}
	return &payload{zip: zr}, nil
}

func (p *payload) open(name string) (io.ReadCloser, error) {
	f, err := p.zip.Open(name)
	if err != nil {
		return nil, fmt.Errorf("payload is missing %s: %w", name, err)
	}
	return f, nil
}

func (p *payload) readAll(name string) ([]byte, error) {
	f, err := p.open(name)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return io.ReadAll(f)
}

func (p *payload) configBytes() ([]byte, error) {
	return p.readAll("config.json")
}

// wheelNames lists the payload's wheels/ entries, sorted so extraction order
// never depends on how the payload was assembled.
func (p *payload) wheelNames() []string {
	var names []string
	for _, f := range p.zip.File {
		if strings.HasPrefix(f.Name, "wheels/") && !strings.HasSuffix(f.Name, "/") {
			names = append(names, f.Name)
		}
	}
	slices.Sort(names)
	return names
}
