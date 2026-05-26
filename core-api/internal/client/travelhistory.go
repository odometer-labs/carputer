package client

import (
	"context"

	"github.com/danielgtaylor/huma/v2"
	"github.com/jackc/pgx/v5/pgxpool"
	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
)

type TravelHistory struct {
	Pool *pgxpool.Pool
}

func (t TravelHistory) CreateTravelHistory(ctx context.Context, request *v2.CreateTravelHistoryRequest) (*v2.CreateTravelHistoryResponse, error) {
	_, err := t.Pool.Exec(
		ctx,
		"call gps.create_travel_history($1, $2, $3, $4, $5);",
		request.Body.MinX,
		request.Body.MaxX,
		request.Body.MinY,
		request.Body.MaxY,
		request.Body.TrackID,
	)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to call create_travel_history()", err)
	}

	resp := v2.CreateTravelHistoryResponse{}
	return &resp, nil
}

func (t TravelHistory) ListTravelHistory(ctx context.Context, request *v2.ListTravelHistoryRequest) (*v2.ListTravelHistoryResponse, error) {
	rows, err := t.Pool.Query(ctx, "select * from gps.list_travel_history();")
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to query list_travel_history()", err)
	}
	defer rows.Close()

	resp := v2.ListTravelHistoryResponse{}
	for rows.Next() {
		travelHistory := v2.TravelHistoryResponse{}
		err := rows.Scan(
			&travelHistory.ID,
			&travelHistory.MinX,
			&travelHistory.MaxX,
			&travelHistory.MinY,
			&travelHistory.MaxY,
			&travelHistory.TrackID,
			&travelHistory.CreatedAt,
		)
		if err != nil {
			return nil, huma.Error500InternalServerError("Unable to list travel history", err)
		}

		resp.Body.TravelHistory = append(resp.Body.TravelHistory, travelHistory)
	}

	if err := rows.Err(); err != nil {
		return nil, huma.Error500InternalServerError("Error reading travel history rows", err)
	}

	return &resp, nil
}
