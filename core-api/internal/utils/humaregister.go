package utils

import (
	"net/http"

	"github.com/danielgtaylor/huma/v2"
	"github.com/odometer-labs/carputer/core-api/internal/handler"
)

func RegisterHumaHandlers(api huma.API) {
	huma.Register(
		api,
		huma.Operation{
			OperationID: "root",
			Method:      http.MethodGet,
			Path:        "/v2/root",
			Summary:     "Prints Hello World!",
			Description: "Prints Hello World to you.",
			Tags:        []string{"Root"},
		}, handler.RootHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "Get Position",
			Method:      http.MethodGet,
			Path:        "/v2/position",
			Summary:     "Get Position",
			Description: "Fetches the current position according to the gpsd",
			Tags:        []string{"Position"},
		}, handler.GetPositionHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID:   "Create Track",
			Method:        http.MethodPost,
			Path:          "/v2/tracks",
			Summary:       "Create Track",
			Description:   "Create and starts a track recording. You will be then be able to record track points with the track points endpoint.",
			Tags:          []string{"Tracks"},
			DefaultStatus: http.StatusCreated,
		}, handler.CreateTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "End Track",
			Method:      http.MethodGet,
			Path:        "/v2/tracks",
			Summary:     "End Track",
			Description: "Ends track recording.",
			Tags:        []string{"Tracks"},
		}, handler.EndTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID:   "Add Track Point",
			Method:        http.MethodPost,
			Path:          "/v2/tracks/track-point",
			Summary:       "Add Track Point",
			Description:   "Adds a track point to the current track that you started.",
			Tags:          []string{"Tracks"},
			DefaultStatus: http.StatusCreated,
		}, handler.AddTrackPointHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "List Tracks",
			Method:      http.MethodGet,
			Path:        "/v2/tracks/list-tracks",
			Summary:     "List Tracks",
			Description: "List all tracks.",
			Tags:        []string{"Tracks"},
		}, handler.ListTracksHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "Get Track",
			Method:      http.MethodGet,
			Path:        "/v2/tracks/{track_id}",
			Summary:     "Get Track",
			Description: "Get a track by the track id.",
			Tags:        []string{"Tracks"},
		}, handler.GetTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "Update Track",
			Method:      http.MethodPut,
			Path:        "/v2/tracks/{track_id}",
			Summary:     "Update Track",
			Description: "Update a track's metadata by the track id. This will only update start_time, end_time, and track_name metadata.",
			Tags:        []string{"Tracks"},
		}, handler.UpdateTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "Delete Track",
			Method:      http.MethodDelete,
			Path:        "/v2/tracks/{track_id}",
			Summary:     "Delete Track",
			Description: "Delete a track by the track id.",
			Tags:        []string{"Tracks"},
		}, handler.DeleteTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "List Tracks MVT",
			Method:      http.MethodPost,
			Path:        "/v2/tracks/tracks-mvt/{track_id}",
			Summary:     "List Tracks MVT",
			Description: "List Tracks MVT.",
			Tags:        []string{"Tracks"},
		}, handler.ListTracksMVTHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "Import Track",
			Method:      http.MethodPost,
			Path:        "/v2/tracks/import-track",
			Summary:     "Import Track",
			Description: "Import a Track.",
			Tags:        []string{"Tracks"},
		}, handler.ImportTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID:   "Import Track Point",
			Method:        http.MethodPost,
			Path:          "/v2/tracks/import-track-point/{track_id}",
			Summary:       "Import Track Point",
			Description:   "Import a track point to the specified track.",
			Tags:          []string{"Tracks"},
			DefaultStatus: http.StatusCreated,
		}, handler.ImportTrackPointHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "Check New Road",
			Method:      http.MethodGet,
			Path:        "/v2/tracks/check-new-road",
			Summary:     "Check New Road",
			Description: "Checks if we are currently on a new road.",
			Tags:        []string{"Tracks"},
		}, handler.CheckNewRoadHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "Ingest APRS Packet",
			Method:      http.MethodPost,
			Path:        "/v2/aprs/ingest",
			Summary:     "Ingest APRS Packet",
			Description: "Ingest an APRS Packet",
			Tags:        []string{"APRS"},
		}, handler.IngestAPRSPacketHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "Ingest Raw APRS Packet",
			Method:      http.MethodPost,
			Path:        "/v2/aprs/ingest/raw-aprs",
			Summary:     "Ingest Raw APRS Packet",
			Description: "Ingest a Raw APRS Packet",
			Tags:        []string{"APRS"},
		}, handler.IngestRawAPRSPacketHandler)
}
