package handler

import (
	"context"

	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
	"github.com/odometer-labs/carputer/core-api/internal/client"
	"github.com/odometer-labs/carputer/core-api/internal/postgis"
)

var regionClient client.Region = client.Region{
	Pool: postgis.GetConnectionPool(),
}

func CreateRegionHandler(ctx context.Context, request *v2.CreateRegionRequest) (*v2.CreateRegionResponse, error) {
	return regionClient.CreateRegion(ctx, request)
}

func ListRegionHandler(ctx context.Context, request *v2.ListRegionsRequest) (*v2.ListRegionsResponse, error) {
	return regionClient.ListRegions(ctx, request)
}

func DeleteRegionHandler(ctx context.Context, request *v2.DeleteRegionRequest) (*v2.DeleteRegionResponse, error) {
	return regionClient.DeleteRegion(ctx, request)
}
