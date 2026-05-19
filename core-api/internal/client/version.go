package client

import (
	"context"
	"time"

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
		return nil, huma.Error500InternalServerError("unable to query get_latest_version();", err)
	}

	return &resp, nil
}

func (v Version) GetVersionHistory(ctx context.Context, request *v2.GetLatestVersionRequest) (*v2.GetVersionHistoryResponse, error) {
	rows, err := v.Pool.Query(ctx, "select * from gps.get_version_history();")

	resp := v2.GetVersionHistoryResponse{}
	for rows.Next() {
		var id uint64
		var versionNumber string
		var gitHash *string
		var releaseDate *time.Time

		err := rows.Scan(
			&id,
			&versionNumber,
			&gitHash,
			&releaseDate,
		)
		if err != nil {
			return nil, huma.Error500InternalServerError("unable to parse row data into version history response", err)
		}

		version := v2.Version{
			VersionNumber: versionNumber,
			GitHash:       gitHash,
			ReleaseDate:   releaseDate,
		}

		resp.Body.Versions = append(resp.Body.Versions, version)
	}

	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("get latest version retrieved no rows", err)
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("unable to query get_version_history()", err)
	}

	return &resp, nil
}
