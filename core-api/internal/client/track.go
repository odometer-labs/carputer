package client

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/jackc/pgx/v5/pgxpool"
	v1 "github.com/odometer-labs/carputer/core-api/api/rest/v1"
	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
)

const GetLongLatUrl = "http://api:8888/v1/get-current-pos"

type Track struct {
	Pool *pgxpool.Pool
}

func (t Track) GetPosition(ctx context.Context) (*v2.GetPositionResponse, error) {
	var longitude float64 = 0.0
	var latitude float64 = 0.0
	var speed float64 = 0.0
	var heading float64 = 0.0

	resp, err := http.Get(GetLongLatUrl)
	if err != nil {
		return nil, fmt.Errorf("failed to get position: %w", err)
	}

	var v1Resp v1.GetPositionV1Response
	err = json.NewDecoder(resp.Body).Decode(&v1Resp)
	if err != nil {
		return nil, fmt.Errorf("failed to serialize v1 response %w", err)
	}

	v2Resp := v2.GetPositionResponse{}

	v2Resp.Body.Longitude = longitude
	v2Resp.Body.Latitude = latitude
	v2Resp.Body.Speed = speed
	v2Resp.Body.Heading = heading

	return &v2Resp, nil
}

func (t Track) ListTracks(ctx context.Context) {}

func (t Track) ListTracksMvt(ctx context.Context) {}

func (t Track) GetTrack(ctx context.Context) {}

func (t Track) UpdateTrack(ctx context.Context) {}

func (t Track) DeleteTrack(ctx context.Context) {}

func (t Track) CreateTrack(ctx context.Context) (*v2.StartTrackResponse, error) {
	var trackId int64

	err := t.Pool.QueryRow(ctx, "select gps.create_track();").Scan(&trackId)
	if err != nil {
		return nil, fmt.Errorf("failed to create track: %w", err)
	}

	resp := v2.StartTrackResponse{}
	resp.Body.ID = trackId

	return &resp, nil
}

func (t Track) EndTrack(ctx context.Context) (*v2.EndTrackResponse, error) {
	_, err := t.Pool.Exec(ctx, "call gps.end_track();")
	if err != nil {
		return nil, fmt.Errorf("failed to end track: %w", err)
	}

	resp := v2.EndTrackResponse{}

	return &resp, nil
}

func (t Track) ImportTrackPoint(ctx context.Context) {}

func (t Track) AddTrackPoint(ctx context.Context) {}

func (t Track) GetLatestTrackPoint(ctx context.Context) {}

func (t Track) CheckNewRoad(ctx context.Context) {}

func (t Track) ImportTrack(ctx context.Context) {}
