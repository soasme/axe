package main

import (
	"archive/tar"
	"archive/zip"
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

// uvTarget maps GOOS/GOARCH to the artifact name in astral-sh/uv releases.
func uvTarget() (string, error) {
	switch runtime.GOOS + "/" + runtime.GOARCH {
	case "linux/amd64":
		return "uv-x86_64-unknown-linux-gnu", nil
	case "linux/arm64":
		return "uv-aarch64-unknown-linux-gnu", nil
	case "darwin/amd64":
		return "uv-x86_64-apple-darwin", nil
	case "darwin/arm64":
		return "uv-aarch64-apple-darwin", nil
	case "windows/amd64":
		return "uv-x86_64-pc-windows-msvc", nil
	}
	return "", fmt.Errorf("unsupported platform %s/%s", runtime.GOOS, runtime.GOARCH)
}

func uvExeName() string {
	if runtime.GOOS == "windows" {
		return "uv.exe"
	}
	return "uv"
}

// ensureUV returns the path to a uv binary of the pinned version, downloading
// and caching it if necessary. AXE_UV overrides everything (tests, air-gapped
// setups).
func ensureUV(version string) (string, error) {
	if override := os.Getenv("AXE_UV"); override != "" {
		return override, nil
	}

	cache, err := cacheDir()
	if err != nil {
		return "", err
	}
	uvPath := filepath.Join(cache, "uv", version, uvExeName())
	if _, err := os.Stat(uvPath); err == nil {
		return uvPath, nil
	}

	statusf("downloading uv %s...", version)
	if err := downloadUV(version, uvPath); err != nil {
		return "", fmt.Errorf("downloading uv %s: %w", version, err)
	}
	return uvPath, nil
}

func downloadUV(version, dest string) error {
	target, err := uvTarget()
	if err != nil {
		return err
	}
	ext := ".tar.gz"
	if runtime.GOOS == "windows" {
		ext = ".zip"
	}
	base := fmt.Sprintf("https://github.com/astral-sh/uv/releases/download/%s/%s%s", version, target, ext)

	archive, err := fetch(base)
	if err != nil {
		return err
	}
	if err := verifyChecksum(archive, base+".sha256"); err != nil {
		return err
	}

	var binary []byte
	if ext == ".zip" {
		binary, err = extractZipMember(archive, uvExeName())
	} else {
		binary, err = extractTarGzMember(archive, uvExeName())
	}
	if err != nil {
		return err
	}

	if err := os.MkdirAll(filepath.Dir(dest), 0o755); err != nil {
		return err
	}
	tmp := dest + fmt.Sprintf(".tmp-%d", os.Getpid())
	if err := os.WriteFile(tmp, binary, 0o755); err != nil {
		return err
	}
	if err := os.Rename(tmp, dest); err != nil {
		os.Remove(tmp)
		// Another process may have won the race; that's fine.
		if _, statErr := os.Stat(dest); statErr == nil {
			return nil
		}
		return err
	}
	return nil
}

func fetch(url string) ([]byte, error) {
	client := &http.Client{Timeout: 10 * time.Minute}
	resp, err := client.Get(url)
	if err != nil {
		return nil, fmt.Errorf("network error fetching %s: %w", url, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("GET %s: %s", url, resp.Status)
	}
	return io.ReadAll(resp.Body)
}

func verifyChecksum(data []byte, checksumURL string) error {
	sums, err := fetch(checksumURL)
	if err != nil {
		return fmt.Errorf("fetching checksum: %w", err)
	}
	fields := strings.Fields(string(sums))
	if len(fields) == 0 {
		return errors.New("empty checksum file")
	}
	want := strings.ToLower(fields[0])
	got := sha256.Sum256(data)
	if hex.EncodeToString(got[:]) != want {
		return errors.New("uv download checksum mismatch")
	}
	return nil
}

func extractTarGzMember(archive []byte, name string) ([]byte, error) {
	gz, err := gzip.NewReader(bytes.NewReader(archive))
	if err != nil {
		return nil, err
	}
	defer gz.Close()
	tr := tar.NewReader(gz)
	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		if filepath.Base(hdr.Name) == name && hdr.Typeflag == tar.TypeReg {
			return io.ReadAll(tr)
		}
	}
	return nil, fmt.Errorf("%s not found in archive", name)
}

func extractZipMember(archive []byte, name string) ([]byte, error) {
	zr, err := zip.NewReader(bytes.NewReader(archive), int64(len(archive)))
	if err != nil {
		return nil, err
	}
	for _, f := range zr.File {
		if filepath.Base(f.Name) == name {
			rc, err := f.Open()
			if err != nil {
				return nil, err
			}
			defer rc.Close()
			return io.ReadAll(rc)
		}
	}
	return nil, fmt.Errorf("%s not found in archive", name)
}
