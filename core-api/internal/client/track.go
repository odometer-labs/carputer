package client

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/danielgtaylor/huma/v2"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	v1 "github.com/odometer-labs/carputer/core-api/api/rest/v1"
	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
)

const GetLongLatUrl = "http://api:8888/ws/get-current-pos"

type Track struct {
	Pool *pgxpool.Pool
}

// GetPosition retrieves the current GPS position from the upstream v1 position
// service at GetLongLatUrl, decodes the JSON response, and returns it as a v2
// response. Returns a 500 if the HTTP request or JSON decoding fails.
func (t Track) GetPosition(ctx context.Context) (*v2.GetPositionResponse, error) {
	var longitude float64 = 0.0
	var latitude float64 = 0.0
	var speed float64 = 0.0
	var heading float64 = 0.0

	resp, err := http.Get(GetLongLatUrl)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to get position", err)
	}

	var v1Resp v1.GetPositionV1Response
	err = json.NewDecoder(resp.Body).Decode(&v1Resp)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to get position", err)
	}

	v2Resp := v2.GetPositionResponse{}

	v2Resp.Body.Longitude = longitude
	v2Resp.Body.Latitude = latitude
	v2Resp.Body.Speed = speed
	v2Resp.Body.Heading = heading

	return &v2Resp, nil
}

// ListTracks returns all tracks from the database by calling gps.view_all_tracks().
// Returns a 404 if no rows are found, or a 500 if the query or any row scan fails.
func (t Track) ListTracks(ctx context.Context, request *v2.ViewAllTracksRequest) (*v2.ViewAllTracksResponse, error) {
	rows, err := t.Pool.Query(ctx, "select * from gps.view_all_tracks();")
	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("No rows from gps.view_all_tracks()", err)
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to list tracks", err)
	}

	resp := &v2.ViewAllTracksResponse{}

	for rows.Next() {
		var item v2.Track

		err := rows.Scan(&item.TrackID, &item.Geom, &item.StartTime, &item.EndTime, &item.TrackName)
		if err != nil {
			return nil, huma.Error500InternalServerError("Unable to list tracks", err)
		}

		resp.Body = append(resp.Body, item)
	}

	return resp, nil
}

// ListTracksMVT returns a Mapbox Vector Tile (MVT) for the given tile coordinates
// (Z, X, Y) and optional filtering parameters (Mode, TrackID, WithinMeters) by
// calling gps.get_tracks_mvt(). Returns a 404 if no rows are found, or a 500 on
// any other query or scan failure.
func (t Track) ListTracksMVT(ctx context.Context, request *v2.ListTracksMVTRequest) (*v2.ListTracksMVTResponse, error) {
	resp := v2.ListTracksMVTResponse{}
	body := request.Body

	err := t.Pool.QueryRow(
		ctx,
		"select * from gps.get_tracks_mvt($1, $2, $3, $4, $5, $6)",
		body.Z,
		body.X,
		body.Y,
		body.Mode,
		request.TrackID,
		body.WithinMeters,
	).Scan(&resp.Body.Bytes)
	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("No rows from gps.get_tracks_mvt()", err)
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to get track mvt", err)
	}

	return &resp, nil
}

// GetTrack retrieves a single track by its TrackID by calling gps.retrieve_track(),
// returning geometry in both native and Web Mercator projections along with its
// time bounds and name. Returns a 404 on any query or scan failure.
func (t Track) GetTrack(ctx context.Context, path *v2.GetTrackPath) (*v2.GetTrackResponse, error) {
	resp := v2.GetTrackResponse{}

	err := t.Pool.QueryRow(ctx, "select * from gps.retrieve_track($1)", path.TrackID).Scan(
		&resp.Body.TrackID,
		&resp.Body.Geom,
		&resp.Body.GeomWM,
		&resp.Body.StartTime,
		&resp.Body.EndTime,
		&resp.Body.TrackName,
	)
	if err != nil {
		return nil, huma.Error404NotFound("No rows from gps.retrieve_track()", err)
	}

	return &resp, nil
}

// UpdateTrack updates the start time, end time, and name of an existing track
// identified by TrackID via the gps.update_track() stored procedure. Returns a 500
// if the database call fails.
func (t Track) UpdateTrack(
	ctx context.Context,
	request *v2.UpdateTrackRequest,
) (*v2.UpdateTrackResponse, error) {

	_, err := t.Pool.Exec(
		ctx,
		"call gps.update_track($1, $2, $3, $4);",
		request.TrackID,
		request.Body.StartTime,
		request.Body.EndTime,
		request.Body.TrackName)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to update track", err)
	}

	resp := v2.UpdateTrackResponse{}
	return &resp, nil
}

// DeleteTrack permanently removes a track from the database by its TrackID via the
// gps.delete_track() stored procedure. Returns a 500 if the database call fails.
func (t Track) DeleteTrack(ctx context.Context, request *v2.DeleteTrackRequest) (*v2.DeleteTrackResponse, error) {
	_, err := t.Pool.Exec(ctx, "call gps.delete_track($1);", request.TrackID)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to delete track", err)
	}

	resp := v2.DeleteTrackResponse{}
	return &resp, nil
}

// CreateTrack creates a new track in the database via gps.create_track(), optionally
// accepting a track name. If no name is provided, the stored procedure is called
// without arguments. Returns the new track's ID, a 404 if no rows are returned, or
// a 500 on any other database error.
func (t Track) CreateTrack(ctx context.Context, request *v2.CreateTrackRequest) (*v2.CreateTrackResponse, error) {
	var trackID int64
	var trackName *string = request.Body.TrackName

	if trackName != nil {
		err := t.Pool.QueryRow(ctx, "select gps.create_track($1);", trackName).Scan(&trackID)
		if err == pgx.ErrNoRows {
			return nil, huma.Error404NotFound("No rows from gps.create_track()", err)
		}
		if err != nil {
			return nil, huma.Error500InternalServerError("Unable to create track", err)
		}
	} else {
		err := t.Pool.QueryRow(ctx, "select gps.create_track();").Scan(&trackID)
		if err == pgx.ErrNoRows {
			return nil, huma.Error404NotFound("No rows from gps.create_track()", err)
		}
		if err != nil {
			return nil, huma.Error500InternalServerError("Unable to create track", err)
		}
	}

	resp := v2.CreateTrackResponse{}
	resp.Body.ID = trackID

	return &resp, nil
}

// EndTrack marks the currently active track as ended by calling gps.end_track().
// Returns a 500 if the database call fails.
func (t Track) EndTrack(ctx context.Context) (*v2.EndTrackResponse, error) {
	_, err := t.Pool.Exec(ctx, "call gps.end_track();")
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to stop track", err)
	}

	resp := v2.EndTrackResponse{}

	return &resp, nil
}

// ImportTrack creates a new track record in the database for import purposes by
// calling gps.import_track(), returning the new track's ID. Returns a 404 if no
// rows are returned, or a 500 on any other database error.
func (t Track) ImportTrack(ctx context.Context, request *v2.ImportTrackRequest) (*v2.ImportTrackResponse, error) {
	var trackID int64

	err := t.Pool.QueryRow(ctx, "select gps.import_track($1);", request.Body.GeoJSONData).Scan(&trackID)
	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("No rows from gps.import_track()", err)
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to import track", err)
	}

	resp := v2.ImportTrackResponse{}
	resp.Body.ID = trackID
	return &resp, nil
}

// ImportTrackPoint appends a single track point to the specified track by calling
// gps.add_track_point() with the current UTC time and the provided latitude,
// longitude, speed, and heading. Returns a 500 if the database call fails.
func (t Track) ImportTrackPoint(ctx context.Context, request *v2.ImportTrackPointRequest) (*v2.ImportTrackPointResponse, error) {
	body := request.Body
	_, err := t.Pool.Exec(
		ctx,
		"call gps.add_track_point($1, $2, $3, $4, $5, $6)",
		request.TrackID,
		time.Now().UTC(),
		body.Latitude,
		body.Longitude,
		body.Speed,
		body.Heading,
	)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to import track point", err)
	}

	resp := v2.ImportTrackPointResponse{}
	return &resp, nil
}

// AddTrackPoint appends a track point to the currently active track (no explicit
// TrackID) by calling gps.add_track_point() with the current UTC time and the
// provided latitude, longitude, speed, and heading. Returns a 500 if the database
// call fails.
func (t Track) AddTrackPoint(ctx context.Context, request *v2.AddTrackPointRequest) (*v2.AddTrackPointResponse, error) {
	body := request.Body

	_, err := t.Pool.Exec(
		ctx,
		"call gps.add_track_point($1, $2, $3, $4, $5)",
		time.Now().UTC(),
		body.Latitude,
		body.Longitude,
		body.Speed,
		body.Heading,
	)
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to add track point", err)
	}

	resp := v2.AddTrackPointResponse{}
	return &resp, nil
}

// CheckNewRoad queries gps.is_new_road() to determine whether the current position
// falls on a road not previously tracked. Returns a 404 if no rows are returned, or
// a 500 on any other database error.
func (t Track) CheckNewRoad(ctx context.Context, request *v2.CheckNewRoadRequest) (*v2.CheckNewRoadResponse, error) {
	var isNewRoad bool

	err := t.Pool.QueryRow(ctx, "select gps.is_new_road();").Scan(&isNewRoad)
	if err == pgx.ErrNoRows {
		return nil, huma.Error404NotFound("No rows from gps.is_new_road()", err)
	}
	if err != nil {
		return nil, huma.Error500InternalServerError("Unable to check new road", err)
	}

	resp := v2.CheckNewRoadResponse{}
	return &resp, nil
}
