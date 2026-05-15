package client

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	v1 "github.com/odometer-labs/carputer/core-api/api/rest/v1"
	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
)

const GetLongLatUrl = "http://api:8888/ws/get-current-pos"

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

func (t Track) ListTracks(ctx context.Context, request *v2.ViewAllTracksRequest) (*v2.ViewAllTracksResponse, error) {
	rows, err := t.Pool.Query(ctx, "select * from gps.view_all_tracks();")
	if err != nil {
		return nil, fmt.Errorf("failed to list tracks: %w", err)
	}

	resp := &v2.ViewAllTracksResponse{}

	for rows.Next() {
		var item v2.Track

		err := rows.Scan(&item.TrackID, &item.Geom, &item.StartTime, &item.EndTime, &item.TrackName)
		if err != nil {
			return nil, err
		}

		resp.Body = append(resp.Body, item)
	}

	return resp, nil
}

func (t Track) ListTracksMvt(ctx context.Context) {}

func (t Track) GetTrack(ctx context.Context, path *v2.GetTrackPath) (*v2.GetTrackResponse, error) {
	resp := v2.GetTrackResponse{}

	err := t.Pool.QueryRow(ctx, "select * from gps.retrieve_track($1)", path.TrackID).Scan(
		&resp.Body.TrackID,
		&resp.Body.Geom,
		&resp.Body.GeomWM,
		&resp.Body.StartTime,
		&resp.Body.EndTime,
		&resp.Body.TrackName,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to get track: %w", err)
	}

	return &resp, nil
}

func (t Track) UpdateTrack(
	ctx context.Context,
	request *v2.UpdateTrackRequest,
) (*v2.UpdateTrackResponse, error) {

	_, err := t.Pool.Exec(
		ctx,
		"call gps.update_track($1, $2, $3, $4);",
		request.TrackID,
		request.Body.StartTime,
		request.Body.EndTime,
		request.Body.TrackName)
	if err != nil {
		return nil, fmt.Errorf("failed to update track: %w", err)
	}

	resp := v2.UpdateTrackResponse{}
	return &resp, nil
}

func (t Track) DeleteTrack(ctx context.Context) {}

func (t Track) CreateTrack(ctx context.Context, request *v2.CreateTrackRequest) (*v2.CreateTrackResponse, error) {
	var trackId int64
	var trackName *string = request.Body.TrackName

	if trackName != nil {
		err := t.Pool.QueryRow(ctx, "select gps.create_track($1);", trackName).Scan(&trackId)
		if err != nil {
			return nil, fmt.Errorf("failed to create track: %w", err)
		}
	} else {
		err := t.Pool.QueryRow(ctx, "select gps.create_track();").Scan(&trackId)
		if err != nil {
			return nil, fmt.Errorf("failed to create track: %w", err)
		}
	}

	resp := v2.CreateTrackResponse{}
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

func (t Track) AddTrackPoint(ctx context.Context, request *v2.AddTrackPointRequest) (*v2.AddTrackPointResponse, error) {
	body := request.Body

	_, err := t.Pool.Exec(
		ctx,
		"call gps.add_track_point($1, $2, $3, $4, $5)",
		time.Now().UTC(),
		body.Latitude,
		body.Longitude,
		body.Speed,
		body.Heading,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to add track point: %w", err)
	}

	resp := v2.AddTrackPointResponse{}
	return &resp, nil
}

func (t Track) GetLatestTrackPoint(ctx context.Context) {}

func (t Track) CheckNewRoad(ctx context.Context) {}

func (t Track) ImportTrack(ctx context.Context) {}
