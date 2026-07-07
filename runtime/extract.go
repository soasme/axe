package main

// Archive extraction for the embedded payload: the python-build-standalone
// tarball, the uv release archive, and the wheels directory.

import (
	"archive/tar"
	"archive/zip"
	"bytes"
	"compress/gzip"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// safeJoin joins an archive entry name onto dest, rejecting traversal.
func safeJoin(dest, name string) (string, error) {
	cleaned := filepath.Clean(filepath.FromSlash(name))
	if filepath.IsAbs(cleaned) || cleaned == ".." || strings.HasPrefix(cleaned, ".."+string(os.PathSeparator)) {
		return "", fmt.Errorf("archive entry escapes destination: %s", name)
	}
	return filepath.Join(dest, cleaned), nil
}

// untarGz extracts a gzipped tarball into dest, stripping the first path
// component (python-build-standalone tarballs wrap everything in "python/").
// Regular files, directories, symlinks, and hard links are supported.
func untarGz(r io.Reader, dest string, stripPrefix bool) error {
	gz, err := gzip.NewReader(r)
	if err != nil {
		return err
	}
	defer gz.Close()

	strip := func(name string) string {
		if !stripPrefix {
			return name
		}
		if _, rest, ok := strings.Cut(name, "/"); ok {
			return rest
		}
		return ""
	}

	tr := tar.NewReader(gz)
	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
		name := strip(hdr.Name)
		if name == "" {
			continue
		}
		path, err := safeJoin(dest, name)
		if err != nil {
			return err
		}
		switch hdr.Typeflag {
		case tar.TypeDir:
			if err := os.MkdirAll(path, 0o755); err != nil {
				return err
			}
		case tar.TypeReg:
			if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
				return err
			}
			f, err := os.OpenFile(path, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, os.FileMode(hdr.Mode)&0o777)
			if err != nil {
				return err
			}
			if _, err := io.Copy(f, tr); err != nil {
				f.Close()
				return err
			}
			if err := f.Close(); err != nil {
				return err
			}
		case tar.TypeSymlink:
			if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
				return err
			}
			os.Remove(path)
			if err := os.Symlink(hdr.Linkname, path); err != nil {
				return err
			}
		case tar.TypeLink:
			target, err := safeJoin(dest, strip(hdr.Linkname))
			if err != nil {
				return err
			}
			os.Remove(path)
			if err := os.Link(target, path); err != nil {
				return err
			}
		}
	}
}

// archiveMember pulls a single file out of a uv release archive (tar.gz on
// unix, zip on windows), matching by base name.
func archiveMember(archiveName string, data []byte, member string) ([]byte, error) {
	if strings.HasSuffix(archiveName, ".zip") {
		zr, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
		if err != nil {
			return nil, err
		}
		for _, f := range zr.File {
			if filepath.Base(f.Name) == member {
				rc, err := f.Open()
				if err != nil {
					return nil, err
				}
				defer rc.Close()
				return io.ReadAll(rc)
			}
		}
		return nil, fmt.Errorf("%s not found in %s", member, archiveName)
	}

	gz, err := gzip.NewReader(bytes.NewReader(data))
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
		if hdr.Typeflag == tar.TypeReg && filepath.Base(hdr.Name) == member {
			return io.ReadAll(tr)
		}
	}
	return nil, fmt.Errorf("%s not found in %s", member, archiveName)
}
