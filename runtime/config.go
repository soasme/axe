package main

import (
	"encoding/json"
	"fmt"
	"slices"
)

type entrypoint struct {
	// "script": console script installed by the wheel
	// "module": python -I -m <value>
	// "spec":   "pkg.mod:func"
	Kind  string `json:"kind"`
	Value string `json:"value"`
}

type config struct {
	Name          string     `json:"name"`
	Version       string     `json:"version"`
	Entrypoint    entrypoint `json:"entrypoint"`
	PythonVersion string     `json:"python_version"`
	UVVersion     string     `json:"uv_version"`
	Expose        []string   `json:"expose"`
	// nil means enabled: configs written before this key existed keep the
	// reserved `self` group.
	SelfCommandGroup *bool  `json:"self_command_group"`
	Fingerprint      string `json:"fingerprint"`
	WheelName        string `json:"wheel_name"`
	UVArchive        string `json:"uv_archive"`
	PythonArchive    string `json:"python_archive"`
}

func parseConfig(data []byte) (*config, error) {
	var c config
	if err := json.Unmarshal(data, &c); err != nil {
		return nil, fmt.Errorf("corrupt embedded config: %w", err)
	}
	for _, field := range []struct{ name, value string }{
		{"name", c.Name},
		{"version", c.Version},
		{"entrypoint", c.Entrypoint.Value},
		{"python_version", c.PythonVersion},
		{"uv_version", c.UVVersion},
		{"fingerprint", c.Fingerprint},
		{"wheel_name", c.WheelName},
		{"uv_archive", c.UVArchive},
		{"python_archive", c.PythonArchive},
	} {
		if field.value == "" {
			return nil, fmt.Errorf("embedded config is missing %q", field.name)
		}
	}
	return &c, nil
}

func (c *config) exposed(command string) bool {
	return slices.Contains(c.Expose, command)
}

func (c *config) selfEnabled() bool {
	return c.SelfCommandGroup == nil || *c.SelfCommandGroup
}
