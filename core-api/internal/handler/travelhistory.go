package handler

import (
	"context"

	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
	"github.com/odometer-labs/carputer/core-api/internal/client"
	"github.com/odometer-labs/carputer/core-api/internal/postgis"
)

var travelHistory = client.TravelHistory{
	Pool: postgis.GetConnectionPool(),
}

func CreateTravelHistoryHandler(ctx context.Context, request *v2.CreateTravelHistoryRequest) (*v2.CreateTravelHistoryResponse, error) {
	resp, err := travelHistory.CreateTravelHistory(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}

func ListTravelHistoryHandler(ctx context.Context, request *v2.ListTravelHistoryRequest) (*v2.ListTravelHistoryResponse, error) {
	resp, err := travelHistory.ListTravelHistory(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}
