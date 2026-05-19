package handler

import (
	"context"

	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
	"github.com/odometer-labs/carputer/core-api/internal/client"
	"github.com/odometer-labs/carputer/core-api/internal/postgis"
)

var version client.Version = client.Version{
	Pool: postgis.GetConnectionPool(),
}

func CreateNewVersionHandler(ctx context.Context, request *v2.CreateNewVersionRequest) (*v2.CreateNewVersionResponse, error) {
	resp, err := version.CreateNewVersion(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}

func GetLatestVersionHandler(ctx context.Context, request *v2.GetLatestVersionRequest) (*v2.GetLatestVersionResponse, error) {
	resp, err := version.GetLatestVersion(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}

func GetVersionHistoryHandler(ctx context.Context, request *v2.GetLatestVersionRequest) (*v2.GetVersionHistoryResponse, error) {
	resp, err := version.GetVersionHistory(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}
