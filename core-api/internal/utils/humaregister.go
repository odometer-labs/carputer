package utils

import (
	"net/http"

	"github.com/danielgtaylor/huma/v2"
	"github.com/odometer-labs/carputer/core-api/internal/handler"
)

const API_VERSION = "/v2"
const LEGACY_API_VERSION = "/v1"

func RegisterHumaHandlers(api huma.API) {
	v2Grp := huma.NewGroup(api, API_VERSION)
	v1Grp := huma.NewGroup(api, LEGACY_API_VERSION)

	huma.Register(
		v2Grp,
		huma.Operation{
			OperationID: "root",
			Method:      http.MethodGet,
			Path:        "/root",
			Summary:     "Prints Hello World!",
			Description: "Prints Hello World to you.",
			Tags:        []string{"Root"},
		}, handler.RootHandler)

	huma.Register(
		v1Grp,
		huma.Operation{
			OperationID: "get-position",
			Method:      http.MethodGet,
			Path:        "/position",
			Summary:     "Get Position",
			Description: "Fetches the current position from the gpsd service. This endpoint calls the v1 legacy endpoint.",
			Tags:        []string{"Position"},
		}, handler.GetPositionHandler)

	huma.Register(
		v2Grp,
		huma.Operation{
			OperationID: "get-position-v2",
			Method:      http.MethodGet,
			Path:        "/position",
			Summary:     "Get Position",
			Description: "Fetches the current GPS position.",
			Tags:        []string{"Position"},
		}, handler.GetPositionHandler)

	registerTracksHandlers(v2Grp)
	registerAPRSHandlers(v2Grp)
	registerVersionHandlers(v2Grp)
	registerTravelHistoryHandlers(v2Grp)
	registerRegionHandlers(v2Grp)
}

func registerTracksHandlers(grp *huma.Group) {
	huma.Register(
		grp,
		huma.Operation{
			OperationID:   "create-track",
			Method:        http.MethodPost,
			Path:          "/tracks",
			Summary:       "Create Track",
			Description:   "Create and starts a track recording. You will be then be able to record track points with the track points endpoint.",
			Tags:          []string{"Tracks"},
			DefaultStatus: http.StatusCreated,
		}, handler.CreateTrackHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "end-track",
			Method:      http.MethodGet,
			Path:        "/tracks",
			Summary:     "End Track",
			Description: "Ends track recording.",
			Tags:        []string{"Tracks"},
		}, handler.EndTrackHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID:   "add-track-point",
			Method:        http.MethodPost,
			Path:          "/tracks/track-point",
			Summary:       "Add Track Point",
			Description:   "Adds a track point to the current track that you started.",
			Tags:          []string{"Tracks"},
			DefaultStatus: http.StatusCreated,
		}, handler.AddTrackPointHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "list-tracks",
			Method:      http.MethodGet,
			Path:        "/tracks/list-tracks",
			Summary:     "List Tracks",
			Description: "List all tracks.",
			Tags:        []string{"Tracks"},
		}, handler.ListTracksHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "get-track",
			Method:      http.MethodGet,
			Path:        "/tracks/{track_id}",
			Summary:     "Get Track",
			Description: "Get a track by the track id.",
			Tags:        []string{"Tracks"},
		}, handler.GetTrackHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "update-track",
			Method:      http.MethodPut,
			Path:        "/tracks/{track_id}",
			Summary:     "Update Track",
			Description: "Update a track's metadata by the track id. This will only update start_time, end_time, and track_name metadata.",
			Tags:        []string{"Tracks"},
		}, handler.UpdateTrackHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "delete-track",
			Method:      http.MethodDelete,
			Path:        "/tracks/{track_id}",
			Summary:     "Delete Track",
			Description: "Delete a track by the track id.",
			Tags:        []string{"Tracks"},
		}, handler.DeleteTrackHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "list-tracks-mvt",
			Method:      http.MethodPost,
			Path:        "/tracks/tracks-mvt/{track_id}",
			Summary:     "List Tracks MVT",
			Description: "List Tracks MVT.",
			Tags:        []string{"Tracks"},
		}, handler.ListTracksMVTHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "import-track",
			Method:      http.MethodPost,
			Path:        "/tracks/import-track",
			Summary:     "Import Track",
			Description: "Import a Track.",
			Tags:        []string{"Tracks"},
		}, handler.ImportTrackHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID:   "import-track-point",
			Method:        http.MethodPost,
			Path:          "/tracks/import-track-point/{track_id}",
			Summary:       "Import Track Point",
			Description:   "Import a track point to the specified track.",
			Tags:          []string{"Tracks"},
			DefaultStatus: http.StatusCreated,
		}, handler.ImportTrackPointHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "check-new-road",
			Method:      http.MethodGet,
			Path:        "/tracks/check-new-road",
			Summary:     "Check New Road",
			Description: "Checks if we are currently on a new road.",
			Tags:        []string{"Tracks"},
		}, handler.CheckNewRoadHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "get-latest-track-point",
			Method:      http.MethodGet,
			Path:        "/tracks/latest-track-point",
			Summary:     "Get Latest Track Point",
			Description: "Returns the most recent GPS track point.",
			Tags:        []string{"Tracks"},
		}, handler.GetLatestTrackPointHandler)
}

func registerAPRSHandlers(grp *huma.Group) {
	huma.Register(
		grp,
		huma.Operation{
			OperationID: "ingest-aprs-packet",
			Method:      http.MethodPost,
			Path:        "/aprs/ingest",
			Summary:     "Ingest APRS Packet",
			Description: "Ingest an APRS packet",
			Tags:        []string{"APRS"},
		}, handler.IngestAPRSPacketHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "ingest-raw-aprs-packet",
			Method:      http.MethodPost,
			Path:        "/aprs/ingest/raw-aprs",
			Summary:     "Ingest Raw APRS Packet",
			Description: "Ingest a raw APRS packet",
			Tags:        []string{"APRS"},
		}, handler.IngestRawAPRSPacketHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "get-nearby-aprs-stations",
			Method:      http.MethodPost,
			Path:        "/aprs/stations",
			Summary:     "Get Nearby APRS Stations",
			Description: "Get all nearby APRS stations. You can specify the search distance in kilometers (default is 500000km).",
			Tags:        []string{"APRS"},
		}, handler.GetNearbyStationsHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "get-aprs-station",
			Method:      http.MethodPost,
			Path:        "/aprs/station",
			Summary:     "Get APRS Stations",
			Description: "Get an APRS station. You can specify the search distance in kilometers (default is 500000km).",
			Tags:        []string{"APRS"},
		}, handler.GetNearbyStationsHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "get-aprs-station-history",
			Method:      http.MethodPost,
			Path:        "/aprs/station/history",
			Summary:     "Get APRS Station History",
			Description: "Get an APRS station's history.",
			Tags:        []string{"APRS"},
		}, handler.GetStationHistoryHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "clean-up-aprs-data",
			Method:      http.MethodPost,
			Path:        "/aprs/station/cleanup",
			Summary:     "Clean Up APRS Data",
			Description: "Clean up old APRS data. You can specify the time range.",
			Tags:        []string{"APRS"},
		}, handler.CleanupAPRSDataHandler)
}

func registerVersionHandlers(grp *huma.Group) {
	huma.Register(
		grp,
		huma.Operation{
			OperationID: "create-new-version",
			Method:      http.MethodPost,
			Path:        "/versioning",
			Summary:     "Create New Version",
			Description: "Create a new latest version. Used to keep track of system updates.",
			Tags:        []string{"Versioning"},
		}, handler.CreateNewVersionHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "get-latest-version",
			Method:      http.MethodGet,
			Path:        "/versioning/latest",
			Summary:     "Get Latest Version",
			Description: "Retrive the latest version number of the carputer system.",
			Tags:        []string{"Versioning"},
		}, handler.GetLatestVersionHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "get-version-history",
			Method:      http.MethodGet,
			Path:        "/versioning/history",
			Summary:     "Get Version History",
			Description: "Get a list of version history of the system.",
			Tags:        []string{"Versioning"},
		}, handler.GetVersionHistoryHandler)
}

func registerTravelHistoryHandlers(grp *huma.Group) {
	huma.Register(
		grp,
		huma.Operation{
			OperationID: "create-travel-history",
			Method:      http.MethodPost,
			Path:        "/travel/history",
			Summary:     "Create Travel History",
			Description: "Record a travel to be displayed later on the map of all the roads you went to.",
			Tags:        []string{"Travel History"},
		}, handler.CreateTravelHistoryHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "list-travel-history",
			Method:      http.MethodGet,
			Path:        "/travel/history",
			Summary:     "List Travel History",
			Description: "Get a list of travel history. The list is retrieved in descending order, with the latest travel on top.",
			Tags:        []string{"Travel History"},
		}, handler.ListTravelHistoryHandler)
}

func registerRegionHandlers(grp *huma.Group) {
	huma.Register(
		grp,
		huma.Operation{
			OperationID: "create-region",
			Method:      http.MethodPost,
			Path:        "/region",
			Summary:     "Create Region",
			Description: "Create a region, which is a bounding limit of how much to render our map in the frontend.",
			Tags:        []string{"Region"},
		}, handler.CreateRegionHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "list-regions",
			Method:      http.MethodGet,
			Path:        "/region",
			Summary:     "List Regions",
			Description: "List all regions the user has created. Retrives the list in descending order, with the latest created region on top.",
			Tags:        []string{"Region"},
		}, handler.ListRegionHandler)

	huma.Register(
		grp,
		huma.Operation{
			OperationID: "delete-regions",
			Method:      http.MethodDelete,
			Path:        "/region",
			Summary:     "Delete Region",
			Description: "Delete a region, specified by the id.",
			Tags:        []string{"Region"},
		}, handler.DeleteRegionHandler)
}
