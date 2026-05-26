//go:build integration

package integration

import (
	"context"
	"testing"

	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
	"github.com/odometer-labs/carputer/core-api/internal/client"
)

func TestCreateTravelHistory(t *testing.T) {
	t.Cleanup(func() { truncateTravelHistory(t) })
	ctx := context.Background()
	c := client.TravelHistory{Pool: testPool}

	req := &v2.CreateTravelHistoryRequest{}
	req.Body.MinX = -122.7
	req.Body.MaxX = -122.6
	req.Body.MinY = 45.5
	req.Body.MaxY = 45.6
	req.Body.TrackID = 42

	if _, err := c.CreateTravelHistory(ctx, req); err != nil {
		t.Fatalf("CreateTravelHistory: %v", err)
	}

	// Verify the row was persisted
	var count int
	err := testPool.QueryRow(ctx, "SELECT count(*) FROM gps.travel_history WHERE track_id = $1", 42).Scan(&count)
	if err != nil {
		t.Fatalf("count query: %v", err)
	}
	if count != 1 {
		t.Errorf("expected 1 row in travel_history, got %d", count)
	}
}

func TestListTravelHistory_Empty(t *testing.T) {
	t.Cleanup(func() { truncateTravelHistory(t) })
	ctx := context.Background()
	c := client.TravelHistory{Pool: testPool}

	resp, err := c.ListTravelHistory(ctx, &v2.ListTravelHistoryRequest{})
	if err != nil {
		t.Fatalf("ListTravelHistory on empty table: %v", err)
	}
	if resp.Body.TravelHistory != nil && len(resp.Body.TravelHistory) != 0 {
		t.Errorf("expected empty slice, got %d items", len(resp.Body.TravelHistory))
	}
}

func TestListTravelHistory_OrderedByIDDesc(t *testing.T) {
	t.Cleanup(func() { truncateTravelHistory(t) })
	ctx := context.Background()
	c := client.TravelHistory{Pool: testPool}

	// Insert three entries with distinct bounding boxes
	entries := []struct{ minX, maxX, minY, maxY float64 }{
		{-122.7, -122.6, 45.5, 45.6},
		{-123.0, -122.9, 45.4, 45.5},
		{-121.5, -121.4, 45.8, 45.9},
	}
	for i, e := range entries {
		req := &v2.CreateTravelHistoryRequest{}
		req.Body.MinX = e.minX
		req.Body.MaxX = e.maxX
		req.Body.MinY = e.minY
		req.Body.MaxY = e.maxY
		req.Body.TrackID = int64(i + 1)
		if _, err := c.CreateTravelHistory(ctx, req); err != nil {
			t.Fatalf("CreateTravelHistory %d: %v", i, err)
		}
	}

	resp, err := c.ListTravelHistory(ctx, &v2.ListTravelHistoryRequest{})
	if err != nil {
		t.Fatalf("ListTravelHistory: %v", err)
	}
	if len(resp.Body.TravelHistory) != 3 {
		t.Fatalf("expected 3 entries, got %d", len(resp.Body.TravelHistory))
	}

	// list_travel_history() returns rows ORDER BY id DESC
	for i := 0; i < len(resp.Body.TravelHistory)-1; i++ {
		if resp.Body.TravelHistory[i].ID < resp.Body.TravelHistory[i+1].ID {
			t.Errorf("entries not in descending ID order: index %d (id=%d) before index %d (id=%d)",
				i, resp.Body.TravelHistory[i].ID,
				i+1, resp.Body.TravelHistory[i+1].ID)
		}
	}
}

func TestTravelHistory_FieldsRoundtrip(t *testing.T) {
	t.Cleanup(func() { truncateTravelHistory(t) })
	ctx := context.Background()
	c := client.TravelHistory{Pool: testPool}

	req := &v2.CreateTravelHistoryRequest{}
	req.Body.MinX = -122.71
	req.Body.MaxX = -122.61
	req.Body.MinY = 45.51
	req.Body.MaxY = 45.61
	req.Body.TrackID = 99

	if _, err := c.CreateTravelHistory(ctx, req); err != nil {
		t.Fatalf("CreateTravelHistory: %v", err)
	}

	resp, err := c.ListTravelHistory(ctx, &v2.ListTravelHistoryRequest{})
	if err != nil {
		t.Fatalf("ListTravelHistory: %v", err)
	}
	if len(resp.Body.TravelHistory) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(resp.Body.TravelHistory))
	}

	got := resp.Body.TravelHistory[0]
	if got.MinX != req.Body.MinX {
		t.Errorf("MinX: want %v, got %v", req.Body.MinX, got.MinX)
	}
	if got.MaxX != req.Body.MaxX {
		t.Errorf("MaxX: want %v, got %v", req.Body.MaxX, got.MaxX)
	}
	if got.MinY != req.Body.MinY {
		t.Errorf("MinY: want %v, got %v", req.Body.MinY, got.MinY)
	}
	if got.MaxY != req.Body.MaxY {
		t.Errorf("MaxY: want %v, got %v", req.Body.MaxY, got.MaxY)
	}
	if got.TrackID != req.Body.TrackID {
		t.Errorf("TrackID: want %v, got %v", req.Body.TrackID, got.TrackID)
	}
	if got.CreatedAt.IsZero() {
		t.Error("expected CreatedAt to be set by the database")
	}
}
