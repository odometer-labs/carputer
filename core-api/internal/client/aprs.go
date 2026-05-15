package client

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
)

type APRS struct {
	Pool *pgxpool.Pool
}

func (a APRS) IngestAPRSPacket(ctx context.Context) {}

func (a APRS) IngestRawAPRSPacket(ctx context.Context) {}

func (a APRS) GetNearbyStations(ctx context.Context) {}

func (a APRS) GetStation(ctx context.Context) {}

func (a APRS) GetStationHistory(ctx context.Context) {}

func (a APRS) GetStats(ctx context.Context) {}

func (a APRS) CleanupOldData(ctx context.Context) {}
