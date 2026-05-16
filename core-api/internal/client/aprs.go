package client

import (
	"context"
	"fmt"

	"github.com/danielgtaylor/huma/v2"
	fap "github.com/hessu/go-aprs-fap"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
)

type APRS struct {
	Pool *pgxpool.Pool
}

func (a APRS) IngestAPRSPacket(ctx context.Context, request *v2.UpsertAPRSStationRequest) (*v2.UpsertAPRSStationResponse, error) {
	var callsign string

	err := a.Pool.QueryRow(
		ctx,
		"SELECT gps.upsert_aprs_station($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);",
		request.Body.Callsign,
		request.Body.Latitude,
		request.Body.Longitude,
		request.Body.SymbolTable,
		request.Body.SymbolCode,
		request.Body.Comment,
		request.Body.AltitudeM,
		request.Body.SpeedKnots,
		request.Body.CourseDeg,
		request.Body.RawPacket).Scan(&callsign)
	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("Now rows from gps.upsert_aprs_station()", err)
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to ingest APRS packet", err)
	}

	resp := v2.UpsertAPRSStationResponse{}
	resp.Body.Callsign = callsign

	return &resp, nil
}

func (a APRS) IngestRawAPRSPacket(ctx context.Context, request *v2.IngestRawAPRSPacketRequest) (*v2.UpsertAPRSStationResponse, error) {
	var ingestOk bool = false
	var parseError *string

	// Parse the raw packet
	p, err := fap.Parse(request.Body.RawPacket)
	if err != nil {
		// Log unsuccessful aprs parse
		temp := "Failed to parse raw APRS packet"
		parseError = &temp
		err := a.logRawAPRSPacket(ctx, p.OrigPacket, false, parseError)
		return nil, huma.Error500InternalServerError("Failed to parse raw APRS packet", err)
	}

	// Convert to Rest DTO
	var courseDeg *float64
	if p.Course != nil {
		var temp float64 = float64(*p.Course)
		courseDeg = &temp
	}

	packet := v2.APRSPacketIn{
		Callsign:    p.SrcCallsign,
		Latitude:    p.Latitude,
		Longitude:   p.Longitude,
		SymbolTable: string(p.SymbolTable),
		SymbolCode:  string(p.SymbolCode),
		Comment:     p.Comment,
		AltitudeM:   p.Altitude,
		SpeedKnots:  p.Speed,
		CourseDeg:   courseDeg,
		RawPacket:   p.OrigPacket,
	}

	// Ingest the raw packet
	ingestRequest := v2.UpsertAPRSStationRequest{
		Body: packet,
	}
	resp, err := a.IngestAPRSPacket(ctx, &ingestRequest)

	// Log the successful raw packet
	err = a.logRawAPRSPacket(ctx, packet.RawPacket, ingestOk, parseError)
	if err != nil {
		return nil, fmt.Errorf("Failed to log raw APRS packet: %w", err)
	}

	return resp, nil
}

func (a APRS) GetNearbyStations(ctx context.Context, request *v2.GetAPRSStationsNearRequest) (*v2.GetAPRSStationsNearResponse, error) {
	var meters float64 = 50000

	if request.Body.Meters != nil {
		meters = *request.Body.Meters
	}

	rows, err := a.Pool.Query(ctx, "select * from gps.get_aprs_stations_near($1);", meters)
	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("Now rows from gps.get_aprs_stations_near()", err)
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to get nearby ARPS stations", err)
	}

	var resp v2.GetAPRSStationsNearResponse
	for rows.Next() {
		var aprsStation v2.APRSStation

		err := rows.Scan(
			&aprsStation.Callsign,
			&aprsStation.SymbolTable,
			&aprsStation.SymbolCode,
			&aprsStation.LastComment,
			&aprsStation.LastSeen,
			&aprsStation.Latitude,
			&aprsStation.Longitude,
			&aprsStation.DistanceM,
			&aprsStation.PacketCount,
		)
		if err != nil {
			return nil, fmt.Errorf("Failed to execute rows.Scan() for GetNearbyStations: %w", err)
		}

		resp.Body = append(resp.Body, aprsStation)
	}

	return &resp, nil
}

func (a APRS) GetStation(ctx context.Context, request *v2.GetAPRSStationRequest) (*v2.GetAPRSStationsNearResponse, error) {
	getStationsNearRequest := v2.GetAPRSStationsNearRequest{
		Body: request.Body,
	}

	resp, err := a.GetNearbyStations(ctx, &getStationsNearRequest)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to get ARPS stations", err)
	}

	return resp, nil
}

func (a APRS) GetStationHistory(ctx context.Context, request *v2.GetAPRSStationHistoryRequest) (*v2.GetAPRSStationHistoryResponse, error) {
	rows, err := a.Pool.Query(
		ctx,
		"select * from gps.get_aprs_station_history($1, $2);",
		request.Body.Callsign,
		request.Body.Hours,
	)
	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("Now rows from gps.get_aprs_station_history()", err)
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to get ARPS station history", err)
	}

	resp := v2.GetAPRSStationHistoryResponse{}

	for rows.Next() {
		var aprsStationHistory v2.APRSStationHistory

		rows.Scan(
			&aprsStationHistory.TimeStamp,
			&aprsStationHistory.Latitude,
			&aprsStationHistory.Longitude,
			&aprsStationHistory.AltitudeM,
			&aprsStationHistory.SpeedKnots,
			&aprsStationHistory.CourseDeg,
			&aprsStationHistory.Comment,
		)

		resp.Body = append(resp.Body, aprsStationHistory)
	}

	return &resp, nil
}

func (a APRS) GetAPRSStats(ctx context.Context, request *v2.GetAPRSStatsRequest) (*v2.GetAPRSStatsResponse, error) {
	var resp v2.GetAPRSStatsResponse

	err := a.Pool.QueryRow(ctx, "select * from gps.get_aprs_stats();").Scan(
		&resp.Body.TotalStations,
		&resp.Body.Stations24h,
		&resp.Body.TotalPackets,
		&resp.Body.Packets24h,
	)
	if err == pgx.ErrNoRows {
		return &resp, nil
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("Failed to get APRS Stats: %w", err)
	}

	return &resp, nil
}

func (a APRS) CleanupOldData(ctx context.Context, request *v2.CleanUpOldDataRequest) (*v2.CleanupOldDataResponse, error) {
	_, err := a.Pool.Exec(ctx, "call gps.cleanup_aprs_data($1, $2);", request.Body.HistoryDays, request.Body.RawDays)
	if err != nil {
		return nil, huma.Error500InternalServerError("Failed to cleanup APRS data: %w", err)
	}

	resp := v2.CleanupOldDataResponse{}
	return &resp, nil
}

func (a APRS) logRawAPRSPacket(
	ctx context.Context,
	rawPacket string,
	parsedOk bool,
	parseError *string) error {

	_, err := a.Pool.Exec(
		ctx,
		"call gps.log_aprs_raw_packet($1, $2, $3);",
		rawPacket,
		parsedOk,
		parseError,
	)
	if err != nil {
		return err
	}

	return nil
}
