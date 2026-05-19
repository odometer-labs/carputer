package client

import (
	"context"

	"github.com/danielgtaylor/huma/v2"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
)

type Version struct {
	Pool *pgxpool.Pool
}

func (v Version) CreateNewVersion(ctx context.Context, request *v2.CreateNewVersionRequest) (*v2.CreateNewVersionResponse, error) {
	_, err := v.Pool.Exec(ctx,
		"call gps.create_new_version($1, $2, $3);",
		request.Body.Version.VersionNumber,
		request.Body.Version.GitHash,
		request.Body.Version.ReleaseDate,
	)
	if err != nil {
		return nil, huma.Error500InternalServerError("failed to exec create_new_version()", err)
	}

	resp := v2.CreateNewVersionResponse{}
	return &resp, nil
}

func (v Version) GetLatestVersion(ctx context.Context, request *v2.GetLatestVersionRequest) (*v2.GetLatestVersionResponse, error) {
	resp := v2.GetLatestVersionResponse{}

	err := v.Pool.QueryRow(ctx, "select * from gps.get_latest_version()").Scan(
		&resp.Body.ID,
		&resp.Body.Version.VersionNumber,
		&resp.Body.Version.GitHash,
		&resp.Body.Version.ReleaseDate,
	)
	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("get latest version retrieved no rows", err)
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("unable to query get_latest_version()", err)
	}

	return &resp, nil
}

func (v Version) GetVersionHistory(ctx context.Context, request *v2.GetLatestVersionRequest) (*v2.GetVersionHistoryResponse, error) {
	var id uint64
	resp := v2.GetVersionHistoryResponse{}

	err := v.Pool.QueryRow(ctx, "select * from gps.get_latest_version()").Scan(
		&id,
		&resp.Body.VersionNumber,
		&resp.Body.GitHash,
		&resp.Body.ReleaseDate,
	)
	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("get latest version retrieved no rows", err)
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("unable to query get_latest_version()", err)
	}

	return &resp, nil
}
