package client

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"
	v1 "github.com/odometer-labs/carputer/core-api/api/rest/v1"
)

type Track struct {
	Pool *pgxpool.Pool
}

func (t Track) ListTracks(ctx context.Context) {}

func (t Track) ListTracksMvt(ctx context.Context) {}

func (t Track) GetTrack(ctx context.Context) {}

func (t Track) UpdateTrack(ctx context.Context) {}

func (t Track) DeleteTrack(ctx context.Context) {}

func (t Track) CreateTrack(ctx context.Context) (*v1.StartTrackResponse, error) {
	var trackId int64

	err := t.Pool.QueryRow(ctx, "select gps.create_track();").Scan(&trackId)
	if err != nil {
		return nil, fmt.Errorf("failed to create track: %w", err)
	}

	resp := v1.StartTrackResponse{}
	resp.Body.ID = trackId

	return &resp, nil
}

func (t Track) EndTrack(ctx context.Context) (*v1.EndTrackResponse, error) {
	_, err := t.Pool.Exec(ctx, "call gps.end_track();")
	if err != nil {
		return nil, fmt.Errorf("failed to end track: %w", err)
	}

	resp := v1.EndTrackResponse{}

	return &resp, nil
}

func (t Track) ImportTrackPoint(ctx context.Context) {}

func (t Track) AddTrackPoint(ctx context.Context) {}

func (t Track) GetLatestTrackPoint(ctx context.Context) {}

func (t Track) CheckNewRoad(ctx context.Context) {}

func (t Track) ImportTrack(ctx context.Context) {}
