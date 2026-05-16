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

// IngestAPRSPacket stores an APRS station packet into the database by calling the
// gps.upsert_aprs_station stored procedure. Returns the callsign of the upserted
// station, or a 404 if no rows were returned, or a 500 on any other database error.
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

// IngestRawAPRSPacket parses a raw APRS packet string using the FAP parser, converts
// it into a structured DTO, and delegates to IngestAPRSPacket for storage. The raw
// packet is logged regardless of parse success or failure. Returns a 500 if parsing
// fails or if logging the raw packet fails.
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
	if err != nil {
		return nil, err
	}

	// Log the successful raw packet
	ingestOk = true
	err = a.logRawAPRSPacket(ctx, packet.RawPacket, ingestOk, parseError)
	if err != nil {
		return nil, huma.Error500InternalServerError("Failed to log raw APRS packet", err)
	}

	return resp, nil
}

// GetNearbyStations returns all APRS stations within a given radius (in meters) of
// the server's reference location by calling gps.get_aprs_stations_near(). Defaults
// to 50,000 meters if no radius is specified in the request. Returns a 404 if no
// rows are found, or a 500 on query or scan failure.
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

// GetStation retrieves APRS station data by adapting a GetAPRSStationRequest into a
// GetAPRSStationsNearRequest and delegating to GetNearbyStations. Returns a 500 if
// the underlying station lookup fails.
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

// GetStationHistory returns the position and telemetry history for a given callsign
// over a specified number of hours by calling gps.get_aprs_station_history(). Returns
// a 404 if no rows are found, or a 500 on query failure. Scan errors per row are
// silently ignored; callers should be aware that partial results may be returned.
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

// GetAPRSStats retrieves aggregate statistics from gps.get_aprs_stats(), including
// total and 24-hour counts for both stations and packets. Returns an empty response
// (rather than an error) if no rows are found, or a 500 on any other query or scan
// failure.
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

// CleanupOldData purges stale APRS records by calling the gps.cleanup_aprs_data()
// stored procedure with configurable retention windows: HistoryDays controls how many
// days of position history to retain, and RawDays controls retention of raw packet
// logs. Returns a 500 if the procedure fails.
func (a APRS) CleanupOldData(ctx context.Context, request *v2.CleanUpOldDataRequest) (*v2.CleanupOldDataResponse, error) {
	_, err := a.Pool.Exec(ctx, "call gps.cleanup_aprs_data($1, $2);", request.Body.HistoryDays, request.Body.RawDays)
	if err != nil {
		return nil, huma.Error500InternalServerError("Failed to cleanup APRS data: %w", err)
	}

	resp := v2.CleanupOldDataResponse{}
	return &resp, nil
}

// logRawAPRSPacket persists a raw APRS packet string to the database via the
// gps.log_aprs_raw_packet() stored procedure, recording whether parsing succeeded
// and any associated parse error message. Returns an error if the database call fails.
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
