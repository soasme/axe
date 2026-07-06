package main

// Payload trailer parsing. Must mirror src/axe/trailer.py exactly:
//
//	[stub][wheel][config JSON][u64 wheel off][u64 wheel len]
//	[u64 config off][u64 config len][u32 format version]["AXEBIN01"]

import (
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"os"
)

const (
	trailerMagic         = "AXEBIN01"
	trailerSize          = 8*4 + 4 + 8
	trailerFormatVersion = 1
)

var errNoTrailer = errors.New("no axe payload found in executable (was this binary built with `axe build`?)")

type trailer struct {
	wheelOffset  uint64
	wheelLength  uint64
	configOffset uint64
	configLength uint64
}

func parseTrailer(buf []byte, fileSize int64) (*trailer, error) {
	if len(buf) != trailerSize {
		return nil, errNoTrailer
	}
	if string(buf[trailerSize-8:]) != trailerMagic {
		return nil, errNoTrailer
	}
	t := &trailer{
		wheelOffset:  binary.LittleEndian.Uint64(buf[0:8]),
		wheelLength:  binary.LittleEndian.Uint64(buf[8:16]),
		configOffset: binary.LittleEndian.Uint64(buf[16:24]),
		configLength: binary.LittleEndian.Uint64(buf[24:32]),
	}
	version := binary.LittleEndian.Uint32(buf[32:36])
	if version != trailerFormatVersion {
		return nil, fmt.Errorf("unsupported payload format version %d (runtime supports %d)", version, trailerFormatVersion)
	}
	end := uint64(fileSize) - trailerSize
	if t.wheelOffset+t.wheelLength > end || t.configOffset+t.configLength > end {
		return nil, errors.New("corrupt payload: sections extend past end of file")
	}
	return t, nil
}

// payload gives lazy access to the sections appended to the executable.
type payload struct {
	path    string
	trailer *trailer
}

func openPayload(exePath string) (*payload, error) {
	f, err := os.Open(exePath)
	if err != nil {
		return nil, fmt.Errorf("cannot open own executable: %w", err)
	}
	defer f.Close()

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
	t, err := parseTrailer(buf, info.Size())
	if err != nil {
		return nil, err
	}
	return &payload{path: exePath, trailer: t}, nil
}

func (p *payload) readSection(offset, length uint64) ([]byte, error) {
	f, err := os.Open(p.path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	buf := make([]byte, length)
	if _, err := io.ReadFull(io.NewSectionReader(f, int64(offset), int64(length)), buf); err != nil {
		return nil, err
	}
	return buf, nil
}

func (p *payload) configBytes() ([]byte, error) {
	return p.readSection(p.trailer.configOffset, p.trailer.configLength)
}

func (p *payload) wheelBytes() ([]byte, error) {
	return p.readSection(p.trailer.wheelOffset, p.trailer.wheelLength)
}
