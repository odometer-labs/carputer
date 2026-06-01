//go:build integration

package integration

import (
	"context"
	"testing"

	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
	"github.com/odometer-labs/carputer/core-api/internal/client"
)

func TestCreateTrack(t *testing.T) {
	t.Cleanup(func() { truncateTracks(t) })
	ctx := context.Background()
	c := client.Track{Pool: testPool}

	resp, err := c.CreateTrack(ctx, &v2.CreateTrackRequest{})
	if err != nil {
		t.Fatalf("CreateTrack: %v", err)
	}
	if resp.Body.ID <= 0 {
		t.Errorf("expected positive track ID, got %d", resp.Body.ID)
	}
}

func TestCreateTrack_WithName(t *testing.T) {
	t.Cleanup(func() { truncateTracks(t) })
	ctx := context.Background()
	c := client.Track{Pool: testPool}

	name := "Portland Run"
	req := &v2.CreateTrackRequest{}
	req.Body.TrackName = &name

	createResp, err := c.CreateTrack(ctx, req)
	if err != nil {
		t.Fatalf("CreateTrack: %v", err)
	}

	for _, pt := range []v2.TrackPoint{
		{Latitude: 45.523, Longitude: -122.676, Speed: 10.0, Heading: 90.0},
		{Latitude: 45.524, Longitude: -122.677, Speed: 12.0, Heading: 91.0},
	} {
		if _, err := c.AddTrackPoint(ctx, &v2.AddTrackPointRequest{Body: pt}); err != nil {
			t.Fatalf("AddTrackPoint: %v", err)
		}
	}

	_, err = c.EndTrack(ctx)
	if err != nil {
		t.Fatalf("EndTrack: %v", err)
	}

	getResp, err := c.GetTrack(ctx, &v2.GetTrackPath{TrackID: uint64(createResp.Body.ID)})
	if err != nil {
		t.Fatalf("GetTrack: %v", err)
	}
	if getResp.Body.TrackName == nil || *getResp.Body.TrackName != name {
		t.Errorf("expected track name %q, got %v", name, getResp.Body.TrackName)
	}
}

func TestCreateTrack_IdempotentWhileActive(t *testing.T) {
	t.Cleanup(func() { truncateTracks(t) })
	ctx := context.Background()
	c := client.Track{Pool: testPool}

	first, err := c.CreateTrack(ctx, &v2.CreateTrackRequest{})
	if err != nil {
		t.Fatalf("first CreateTrack: %v", err)
	}

	second, err := c.CreateTrack(ctx, &v2.CreateTrackRequest{})
	if err != nil {
		t.Fatalf("second CreateTrack: %v", err)
	}

	if first.Body.ID != second.Body.ID {
		t.Errorf("expected same track ID for both calls while active, got %d and %d",
			first.Body.ID, second.Body.ID)
	}
}

func TestTrackLifecycle(t *testing.T) {
	t.Cleanup(func() { truncateTracks(t) })
	ctx := context.Background()
	c := client.Track{Pool: testPool}

	// Create
	createResp, err := c.CreateTrack(ctx, &v2.CreateTrackRequest{})
	if err != nil {
		t.Fatalf("CreateTrack: %v", err)
	}
	trackID := uint64(createResp.Body.ID)

	// Add two points so a track line is generated
	for _, pt := range []v2.TrackPoint{
		{Latitude: 45.523, Longitude: -122.676, Speed: 10.0, Heading: 90.0},
		{Latitude: 45.524, Longitude: -122.677, Speed: 12.0, Heading: 91.0},
	} {
		req := &v2.AddTrackPointRequest{Body: pt}
		if _, err := c.AddTrackPoint(ctx, req); err != nil {
			t.Fatalf("AddTrackPoint: %v", err)
		}
	}

	// End
	if _, err := c.EndTrack(ctx); err != nil {
		t.Fatalf("EndTrack: %v", err)
	}

	// Get and verify end_time is set
	getResp, err := c.GetTrack(ctx, &v2.GetTrackPath{TrackID: trackID})
	if err != nil {
		t.Fatalf("GetTrack: %v", err)
	}
	if getResp.Body.TrackID != trackID {
		t.Errorf("track ID: want %d, got %d", trackID, getResp.Body.TrackID)
	}
	if getResp.Body.EndTime == nil || getResp.Body.EndTime.IsZero() {
		t.Error("expected EndTime to be set after EndTrack")
	}
	if getResp.Body.Geom == nil {
		t.Error("expected Geom to be non-nil after adding two points")
	}
}

func TestDeleteTrack(t *testing.T) {
	t.Cleanup(func() { truncateTracks(t) })
	ctx := context.Background()
	c := client.Track{Pool: testPool}

	createResp, err := c.CreateTrack(ctx, &v2.CreateTrackRequest{})
	if err != nil {
		t.Fatalf("CreateTrack: %v", err)
	}
	trackID := uint64(createResp.Body.ID)

	if _, err := c.EndTrack(ctx); err != nil {
		t.Fatalf("EndTrack: %v", err)
	}

	if _, err := c.DeleteTrack(ctx, &v2.DeleteTrackRequest{TrackID: trackID}); err != nil {
		t.Fatalf("DeleteTrack: %v", err)
	}

	// GetTrack should now return an error
	_, err = c.GetTrack(ctx, &v2.GetTrackPath{TrackID: trackID})
	if err == nil {
		t.Error("expected error from GetTrack after delete, got nil")
	}
}

func TestListTracks(t *testing.T) {
	t.Cleanup(func() { truncateTracks(t) })
	ctx := context.Background()
	c := client.Track{Pool: testPool}

	for i := 0; i < 3; i++ {
		if _, err := c.CreateTrack(ctx, &v2.CreateTrackRequest{}); err != nil {
			t.Fatalf("CreateTrack %d: %v", i, err)
		}
		for _, pt := range []v2.TrackPoint{
			{Latitude: 45.523 + float64(i)*0.001, Longitude: -122.676, Speed: 10.0, Heading: 90.0},
			{Latitude: 45.524 + float64(i)*0.001, Longitude: -122.677, Speed: 12.0, Heading: 91.0},
		} {
			if _, err := c.AddTrackPoint(ctx, &v2.AddTrackPointRequest{Body: pt}); err != nil {
				t.Fatalf("AddTrackPoint %d: %v", i, err)
			}
		}
		if _, err := c.EndTrack(ctx); err != nil {
			t.Fatalf("EndTrack %d: %v", i, err)
		}
	}

	listResp, err := c.ListTracks(ctx, &v2.ViewAllTracksRequest{})
	if err != nil {
		t.Fatalf("ListTracks: %v", err)
	}
	if len(listResp.Body.Tracks) < 3 {
		t.Errorf("expected at least 3 tracks, got %d", len(listResp.Body.Tracks))
	}
}

func TestUpdateTrack(t *testing.T) {
	t.Cleanup(func() { truncateTracks(t) })
	ctx := context.Background()
	c := client.Track{Pool: testPool}

	createResp, err := c.CreateTrack(ctx, &v2.CreateTrackRequest{})
	if err != nil {
		t.Fatalf("CreateTrack: %v", err)
	}
	trackID := uint64(createResp.Body.ID)

	newName := "Renamed Track"
	updateReq := &v2.UpdateTrackRequest{TrackID: trackID}
	updateReq.Body.TrackName = &newName

	if _, err := c.UpdateTrack(ctx, updateReq); err != nil {
		t.Fatalf("UpdateTrack: %v", err)
	}

	for _, pt := range []v2.TrackPoint{
		{Latitude: 45.523, Longitude: -122.676, Speed: 10.0, Heading: 90.0},
		{Latitude: 45.524, Longitude: -122.677, Speed: 12.0, Heading: 91.0},
	} {
		if _, err := c.AddTrackPoint(ctx, &v2.AddTrackPointRequest{Body: pt}); err != nil {
			t.Fatalf("AddTrackPoint: %v", err)
		}
	}

	if _, err := c.EndTrack(ctx); err != nil {
		t.Fatalf("EndTrack: %v", err)
	}

	getResp, err := c.GetTrack(ctx, &v2.GetTrackPath{TrackID: trackID})
	if err != nil {
		t.Fatalf("GetTrack: %v", err)
	}
	if getResp.Body.TrackName == nil || *getResp.Body.TrackName != newName {
		t.Errorf("expected track name %q, got %v", newName, getResp.Body.TrackName)
	}
}
