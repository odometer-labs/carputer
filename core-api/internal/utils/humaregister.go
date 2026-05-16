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
			OperationID: "get-position",
			Method:      http.MethodGet,
			Path:        "/v2/position",
			Summary:     "Get Position",
			Description: "Fetches the current position according to the gpsd",
			Tags:        []string{"Position"},
		}, handler.GetPositionHandler)

	registerTracksHandlers(api)
	registerAPRSHandlers(api)
}

func registerTracksHandlers(api huma.API) {
	huma.Register(
		api,
		huma.Operation{
			OperationID:   "create-track",
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
			OperationID: "end-track",
			Method:      http.MethodGet,
			Path:        "/v2/tracks",
			Summary:     "End Track",
			Description: "Ends track recording.",
			Tags:        []string{"Tracks"},
		}, handler.EndTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID:   "add-track-point",
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
			OperationID: "list-tracks",
			Method:      http.MethodGet,
			Path:        "/v2/tracks/list-tracks",
			Summary:     "List Tracks",
			Description: "List all tracks.",
			Tags:        []string{"Tracks"},
		}, handler.ListTracksHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "get-track",
			Method:      http.MethodGet,
			Path:        "/v2/tracks/{track_id}",
			Summary:     "Get Track",
			Description: "Get a track by the track id.",
			Tags:        []string{"Tracks"},
		}, handler.GetTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "update-track",
			Method:      http.MethodPut,
			Path:        "/v2/tracks/{track_id}",
			Summary:     "Update Track",
			Description: "Update a track's metadata by the track id. This will only update start_time, end_time, and track_name metadata.",
			Tags:        []string{"Tracks"},
		}, handler.UpdateTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "delete-track",
			Method:      http.MethodDelete,
			Path:        "/v2/tracks/{track_id}",
			Summary:     "Delete Track",
			Description: "Delete a track by the track id.",
			Tags:        []string{"Tracks"},
		}, handler.DeleteTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "list-tracks-mvt",
			Method:      http.MethodPost,
			Path:        "/v2/tracks/tracks-mvt/{track_id}",
			Summary:     "List Tracks MVT",
			Description: "List Tracks MVT.",
			Tags:        []string{"Tracks"},
		}, handler.ListTracksMVTHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "import-track",
			Method:      http.MethodPost,
			Path:        "/v2/tracks/import-track",
			Summary:     "Import Track",
			Description: "Import a Track.",
			Tags:        []string{"Tracks"},
		}, handler.ImportTrackHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID:   "import-track-point",
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
			OperationID: "check-new-road",
			Method:      http.MethodGet,
			Path:        "/v2/tracks/check-new-road",
			Summary:     "Check New Road",
			Description: "Checks if we are currently on a new road.",
			Tags:        []string{"Tracks"},
		}, handler.CheckNewRoadHandler)
}

func registerAPRSHandlers(api huma.API) {
	huma.Register(
		api,
		huma.Operation{
			OperationID: "ingest-aprs-packet",
			Method:      http.MethodPost,
			Path:        "/v2/aprs/ingest",
			Summary:     "Ingest APRS Packet",
			Description: "Ingest an APRS packet",
			Tags:        []string{"APRS"},
		}, handler.IngestAPRSPacketHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "ingest-raw-aprs-packet",
			Method:      http.MethodPost,
			Path:        "/v2/aprs/ingest/raw-aprs",
			Summary:     "Ingest Raw APRS Packet",
			Description: "Ingest a raw APRS packet",
			Tags:        []string{"APRS"},
		}, handler.IngestRawAPRSPacketHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "get-nearby-aprs-stations",
			Method:      http.MethodPost,
			Path:        "/v2/aprs/stations",
			Summary:     "Get Nearby APRS Stations",
			Description: "Get all nearby APRS stations. You can specify the search distance in kilometers (default is 500000km).",
			Tags:        []string{"APRS"},
		}, handler.GetNearbyStationsHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "get-aprs-station",
			Method:      http.MethodPost,
			Path:        "/v2/aprs/station",
			Summary:     "Get APRS Stations",
			Description: "Get an APRS station. You can specify the search distance in kilometers (default is 500000km).",
			Tags:        []string{"APRS"},
		}, handler.GetNearbyStationsHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "get-aprs-station-history",
			Method:      http.MethodPost,
			Path:        "/v2/aprs/station/history",
			Summary:     "Get APRS Station History",
			Description: "Get an APRS station's history.",
			Tags:        []string{"APRS"},
		}, handler.GetStationHistoryHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "clean-up-aprs-data",
			Method:      http.MethodPost,
			Path:        "/v2/aprs/station/cleanup",
			Summary:     "Clean Up APRS Data",
			Description: "Clean up old APRS data. You can specify the time range.",
			Tags:        []string{"APRS"},
		}, handler.CleanupAPRSDataHandler)
}
