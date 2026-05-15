package handler

import (
	"context"

	"github.com/danielgtaylor/huma/v2"
	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
	"github.com/odometer-labs/carputer/core-api/internal/client"
	"github.com/odometer-labs/carputer/core-api/internal/postgis"
)

var trackClient client.Track = client.Track{
	Pool: postgis.GetConnectionPool(),
}

func GetPositionHandler(ctx context.Context, request *v2.GetPositionRequest) (*v2.GetPositionResponse, error) {
	resp, err := trackClient.GetPosition(ctx)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to get position: %v", err)
	}

	return resp, err
}

func CreateTrackHandler(ctx context.Context, request *v2.CreateTrackRequest) (*v2.CreateTrackResponse, error) {
	resp, err := trackClient.CreateTrack(ctx, request)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to create track: %v", err)
	}

	return resp, err
}

func EndTrackHandler(ctx context.Context, request *v2.EndTrackRequest) (*v2.EndTrackResponse, error) {
	resp, err := trackClient.EndTrack(ctx)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to stop track: %v", err)
	}

	return resp, err
}

func AddTrackPointHandler(ctx context.Context, request *v2.AddTrackPointRequest) (*v2.AddTrackPointResponse, error) {
	resp, err := trackClient.AddTrackPoint(ctx, request)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to add track point: %v", err)
	}

	return resp, err
}

func ListTracksHandler(ctx context.Context, request *v2.ViewAllTracksRequest) (*v2.ViewAllTracksResponse, error) {
	resp, err := trackClient.ListTracks(ctx, request)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to list tracks: %v", err)
	}

	return resp, err
}

func GetTrackHandler(ctx context.Context, path *v2.GetTrackPath) (*v2.GetTrackResponse, error) {
	resp, err := trackClient.GetTrack(ctx, path)
	if err != nil {
		return nil, huma.Error404NotFound("Unable to find or get track: %v", err)
	}

	return resp, err
}

func UpdateTrackHandler(ctx context.Context, request *v2.UpdateTrackRequest) (*v2.UpdateTrackResponse, error) {
	resp, err := trackClient.UpdateTrack(ctx, request)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to update track: %v", err)
	}

	return resp, err
}

func DeleteTrackHandler(ctx context.Context, request *v2.DeleteTrackRequest) (*v2.DeleteTrackResponse, error) {
	resp, err := trackClient.DeleteTrack(ctx, request)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to update track: %v", err)
	}

	return resp, err
}

func ListTracksMVTHandler(ctx context.Context, request *v2.ListTracksMVTRequest) (*v2.ListTracksMVTResponse, error) {
	resp, err := trackClient.ListTracksMVT(ctx, request)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to get track mvt: %v", err)
	}

	return resp, err
}

func ImportTrackHandler(ctx context.Context, request *v2.ImportTrackRequest) (*v2.ImportTrackResponse, error) {
	resp, err := trackClient.ImportTrack(ctx, request)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to import track: %v", err)
	}

	return resp, err
}

func ImportTrackPointHandler(ctx context.Context, request *v2.ImportTrackPointRequest) (*v2.ImportTrackPointResponse, error) {
	resp, err := trackClient.ImportTrackPoint(ctx, request)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to import track point: %v", err)
	}

	return resp, err
}

func CheckNewRoadHandler(ctx context.Context, request *v2.CheckNewRoadRequest) (*v2.CheckNewRoadResponse, error) {
	resp, err := trackClient.CheckNewRoad(ctx, request)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to check new road: %v", err)
	}

	return resp, nil
}
