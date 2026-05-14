package handler

import (
	"context"

	"github.com/danielgtaylor/huma/v2"
	v1 "github.com/odometer-labs/carputer/core-api/api/rest/v1"
	"github.com/odometer-labs/carputer/core-api/internal/client"
	"github.com/odometer-labs/carputer/core-api/internal/postgis"
)

var trackClient client.Track = client.Track{
	Pool: postgis.GetConnectionPool(),
}

func CreateTrackHander(ctx context.Context, request *v1.StartTrackRequest) (*v1.StartTrackResponse, error) {
	resp, err := trackClient.CreateTrack(ctx)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to create track: %v", err)
	}

	return resp, err
}
