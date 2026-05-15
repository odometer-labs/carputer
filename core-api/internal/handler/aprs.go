package handler

import (
	"context"

	"github.com/danielgtaylor/huma/v2"
	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
	"github.com/odometer-labs/carputer/core-api/internal/client"
	"github.com/odometer-labs/carputer/core-api/internal/postgis"
)

var aprsClient client.APRS = client.APRS{
	Pool: postgis.GetConnectionPool(),
}

func IngestAPRSPacketHandler(ctx context.Context, request *v2.UpsertAPRSStationRequest) (*v2.UpsertAPRSStationResponse, error) {
	resp, err := aprsClient.IngestAPRSPacket(ctx, request)
	if err != nil {
		return nil, huma.Error500InternalServerError("")
	}

	return resp, nil
}

func IngestRawAPRSPacketHandler(ctx context.Context) {}

func GetNearbyStationsHandler(ctx context.Context) {}

func GetStationHandler(ctx context.Context) {}

func GetStationHistoryHandler(ctx context.Context) {}

func GetAPRSStatsHandler(ctx context.Context) {}

func CleanupAPRSDataHandler(ctx context.Context) {}
