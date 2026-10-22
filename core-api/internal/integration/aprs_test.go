//go:build integration

package integration

import (
	"context"
	"testing"

	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
	"github.com/odometer-labs/carputer/core-api/internal/client"
)

func newAPRSPacket(callsign string, lat, lon float64) *v2.UpsertAPRSStationRequest {
	req := &v2.UpsertAPRSStationRequest{}
	req.Body.Callsign = callsign
	req.Body.Latitude = &lat
	req.Body.Longitude = &lon
	req.Body.SymbolTable = "/"
	req.Body.SymbolCode = "k"
	req.Body.Comment = "test station"
	req.Body.RawPacket = callsign + ">APRS,TCPIP*:!4533.18N/12240.56W>"
	return req
}

func TestIngestAPRSPacket(t *testing.T) {
	t.Cleanup(func() { truncateAPRS(t) })
	ctx := context.Background()
	c := client.APRS{Pool: testPool}

	resp, err := c.IngestAPRSPacket(ctx, newAPRSPacket("W1ABC", 45.5, -122.6))
	if err != nil {
		t.Fatalf("IngestAPRSPacket: %v", err)
	}
	if resp.Body.Callsign != "W1ABC" {
		t.Errorf("expected callsign W1ABC, got %q", resp.Body.Callsign)
	}
}

func TestIngestAPRSPacket_Upsert(t *testing.T) {
	t.Cleanup(func() { truncateAPRS(t) })
	ctx := context.Background()
	c := client.APRS{Pool: testPool}

	// Ingest same callsign twice
	for i := 0; i < 2; i++ {
		if _, err := c.IngestAPRSPacket(ctx, newAPRSPacket("W2XYZ", 45.5, -122.6)); err != nil {
			t.Fatalf("IngestAPRSPacket %d: %v", i, err)
		}
	}

	// Confirm only one station row and packet_count == 2
	var count int
	var packetCount int
	err := testPool.QueryRow(ctx,
		"SELECT count(*), max(packet_count) FROM gps.aprs_stations WHERE callsign = $1",
		"W2XYZ",
	).Scan(&count, &packetCount)
	if err != nil {
		t.Fatalf("query: %v", err)
	}
	if count != 1 {
		t.Errorf("expected 1 station row, got %d", count)
	}
	if packetCount != 2 {
		t.Errorf("expected packet_count 2, got %d", packetCount)
	}
}

func TestGetNearbyStations_NoGPSFix(t *testing.T) {
	t.Cleanup(func() {
		truncateAPRS(t)
		truncateTracks(t)
	})
	ctx := context.Background()
	c := client.APRS{Pool: testPool}

	// Ingest a few stations
	for _, cs := range []string{"K1AAA", "K1BBB", "K1CCC"} {
		if _, err := c.IngestAPRSPacket(ctx, newAPRSPacket(cs, 45.5, -122.6)); err != nil {
			t.Fatalf("IngestAPRSPacket %s: %v", cs, err)
		}
	}

	// Without a GPS fix, get_aprs_stations_near falls back to returning recent stations
	resp, err := c.GetNearbyStations(ctx, &v2.GetAPRSStationsNearRequest{})
	if err != nil {
		t.Fatalf("GetNearbyStations: %v", err)
	}
	if len(resp.Body.APRSStations) < 3 {
		t.Errorf("expected at least 3 stations, got %d", len(resp.Body.APRSStations))
	}
}

func TestGetStationHistory(t *testing.T) {
	t.Cleanup(func() { truncateAPRS(t) })
	ctx := context.Background()
	c := client.APRS{Pool: testPool}

	// Ingest the same station three times
	for i := 0; i < 3; i++ {
		lat := 45.5 + float64(i)*0.001
		if _, err := c.IngestAPRSPacket(ctx, newAPRSPacket("N0CALL", lat, -122.6)); err != nil {
			t.Fatalf("IngestAPRSPacket %d: %v", i, err)
		}
	}

	req := &v2.GetAPRSStationHistoryRequest{}
	req.Body.Callsign = "N0CALL"
	req.Body.Hours = 24

	resp, err := c.GetStationHistory(ctx, req)
	if err != nil {
		t.Fatalf("GetStationHistory: %v", err)
	}
	if len(resp.Body.APRSStationHistory) != 3 {
		t.Errorf("expected 3 history entries, got %d", len(resp.Body.APRSStationHistory))
	}
}

func TestGetAPRSStats(t *testing.T) {
	t.Cleanup(func() { truncateAPRS(t) })
	ctx := context.Background()
	c := client.APRS{Pool: testPool}

	for _, cs := range []string{"K9AA", "K9BB"} {
		if _, err := c.IngestAPRSPacket(ctx, newAPRSPacket(cs, 45.5, -122.6)); err != nil {
			t.Fatalf("IngestAPRSPacket %s: %v", cs, err)
		}
	}

	resp, err := c.GetAPRSStats(ctx, &v2.GetAPRSStatsRequest{})
	if err != nil {
		t.Fatalf("GetAPRSStats: %v", err)
	}
	if resp.Body.TotalStations < 2 {
		t.Errorf("expected TotalStations >= 2, got %d", resp.Body.TotalStations)
	}
	if resp.Body.TotalPackets < 2 {
		t.Errorf("expected TotalPackets >= 2, got %d", resp.Body.TotalPackets)
	}
}
