//go:build integration

package integration

import (
	"context"
	"testing"
	"time"

	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
	"github.com/odometer-labs/carputer/core-api/internal/client"
)

func TestGetLatestVersion_SeedExists(t *testing.T) {
	// Do not truncate — the seed row '1.0.0' is inserted during DB init.
	ctx := context.Background()
	c := client.Version{Pool: testPool}

	resp, err := c.GetLatestVersion(ctx, &v2.GetLatestVersionRequest{})
	if err != nil {
		t.Fatalf("GetLatestVersion: %v", err)
	}
	if resp.Body.Version.VersionNumber == "" {
		t.Error("expected a non-empty version number from seed data")
	}
}

func TestCreateNewVersion(t *testing.T) {
	t.Cleanup(func() {
		truncateVersions(t)
		// Re-insert seed so other tests remain consistent.
		_, err := testPool.Exec(context.Background(),
			`INSERT INTO gps.version (version_number) VALUES ('1.0.0') ON CONFLICT DO NOTHING`)
		if err != nil {
			t.Logf("re-seed version: %v", err)
		}
	})
	ctx := context.Background()
	c := client.Version{Pool: testPool}

	now := time.Now().UTC()
	hash := "abc123"
	req := &v2.CreateNewVersionRequest{}
	req.Body.Version = v2.Version{
		VersionNumber: "9.9.9",
		GitHash:       &hash,
		ReleaseDate:   &now,
	}

	if _, err := c.CreateNewVersion(ctx, req); err != nil {
		t.Fatalf("CreateNewVersion: %v", err)
	}

	latest, err := c.GetLatestVersion(ctx, &v2.GetLatestVersionRequest{})
	if err != nil {
		t.Fatalf("GetLatestVersion: %v", err)
	}
	if latest.Body.Version.VersionNumber != "9.9.9" {
		t.Errorf("expected latest version 9.9.9, got %q", latest.Body.Version.VersionNumber)
	}
}

func TestGetVersionHistory(t *testing.T) {
	// Do not truncate — seed data guarantees at least one row.
	ctx := context.Background()
	c := client.Version{Pool: testPool}

	resp, err := c.GetVersionHistory(ctx, &v2.GetLatestVersionRequest{})
	if err != nil {
		t.Fatalf("GetVersionHistory: %v", err)
	}
	if len(resp.Body.Versions) == 0 {
		t.Error("expected at least one version in history")
	}
}
