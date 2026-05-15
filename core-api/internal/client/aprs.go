package client

import (
	"context"
	"fmt"

	fap "github.com/hessu/go-aprs-fap"
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
	if err != nil {
		return nil, fmt.Errorf("failed to ingest APRS packet: %w", err)
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
		temp := "failed to parse raw APRS packet"
		parseError = &temp
		err := a.LogRawAPRSPacket(ctx, p.OrigPacket, false, parseError)
		return nil, fmt.Errorf("failed to parse raw APRS packet: %w", err)
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
	err = a.LogRawAPRSPacket(ctx, packet.RawPacket, ingestOk, parseError)
	if err != nil {
		return nil, fmt.Errorf("failed to log raw APRS packet: %w", err)
	}

	return resp, nil
}

func (a APRS) GetNearbyStations(ctx context.Context) {}

func (a APRS) GetStation(ctx context.Context) {}

func (a APRS) GetStationHistory(ctx context.Context) {}

func (a APRS) GetStats(ctx context.Context) {}

func (a APRS) CleanupOldData(ctx context.Context) {}

func (a APRS) LogRawAPRSPacket(
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
