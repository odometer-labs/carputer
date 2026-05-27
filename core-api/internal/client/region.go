package client

import (
	"context"

	"github.com/danielgtaylor/huma/v2"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
)

type Region struct {
	Pool *pgxpool.Pool
}

func (r Region) CreateRegion(ctx context.Context, request *v2.CreateRegionRequest) (*v2.CreateRegionResponse, error) {
	_, err := r.Pool.Exec(
		ctx,
		"call gps.create_region($1, $2, $3, $4, $5);",
		request.Body.MinX,
		request.Body.MaxX,
		request.Body.MinY,
		request.Body.MaxY,
		request.Body.Name,
	)
	if err != nil {
		return nil, huma.Error500InternalServerError("unable to call gps.create_region", err)
	}

	resp := v2.CreateRegionResponse{}
	return &resp, nil
}

func (r Region) ListRegions(ctx context.Context, request *v2.ListRegionsRequest) (*v2.ListRegionsResponse, error) {
	rows, err := r.Pool.Query(ctx, "select * from gps.list_regions();")
	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("no rows from call to gps.list_regions()", err)
	}

	resp := v2.ListRegionsResponse{}
	for rows.Next() {
		var id uint64
		region := v2.Region{}

		err := rows.Scan(
			&id,
			&region.MinX,
			&region.MaxX,
			&region.MinY,
			&region.MaxY,
			&region.Name,
		)
		if err != nil {
			return nil, huma.Error500InternalServerError("unable to parse regions from gps.list_regions()", err)
		}

		resp.Body.Regions = append(resp.Body.Regions, region)
	}

	return &resp, nil
}
