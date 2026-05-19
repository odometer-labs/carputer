package handler

import (
	"context"

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
		return nil, err
	}

	return resp, nil
}

func IngestRawAPRSPacketHandler(ctx context.Context, request *v2.IngestRawAPRSPacketRequest) (*v2.UpsertAPRSStationResponse, error) {
	resp, err := aprsClient.IngestRawAPRSPacket(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}

func GetNearbyStationsHandler(ctx context.Context, request *v2.GetAPRSStationsNearRequest) (*v2.GetAPRSStationsNearResponse, error) {
	resp, err := aprsClient.GetNearbyStations(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}

func GetStationHandler(ctx context.Context, request *v2.GetAPRSStationRequest) (*v2.GetAPRSStationsNearResponse, error) {
	resp, err := aprsClient.GetStation(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}

func GetStationHistoryHandler(ctx context.Context, request *v2.GetAPRSStationHistoryRequest) (*v2.GetAPRSStationHistoryResponse, error) {
	resp, err := aprsClient.GetStationHistory(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}

func GetAPRSStatsHandler(ctx context.Context, request *v2.GetAPRSStatsRequest) (*v2.GetAPRSStatsResponse, error) {
	resp, err := aprsClient.GetAPRSStats(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}

func CleanupAPRSDataHandler(ctx context.Context, request *v2.CleanUpOldDataRequest) (*v2.CleanupOldDataResponse, error) {
	resp, err := aprsClient.CleanupOldData(ctx, request)
	if err != nil {
		return nil, err
	}

	return resp, nil
}
