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

func CreateTrackHander(ctx context.Context, request *v2.StartTrackRequest) (*v2.StartTrackResponse, error) {
	resp, err := trackClient.CreateTrack(ctx)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to create track: %v", err)
	}

	return resp, err
}

func EndTrackHander(ctx context.Context, request *v2.EndTrackRequest) (*v2.EndTrackResponse, error) {
	resp, err := trackClient.EndTrack(ctx)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to stop track: %v", err)
	}

	return resp, err
}
