package main

import (
	"fmt"
	"net/http"

	"github.com/danielgtaylor/huma/v2"
	"github.com/danielgtaylor/huma/v2/adapters/humago"
	"github.com/odometer-labs/carputer/core-api/internal/handler"
	"github.com/odometer-labs/carputer/core-api/internal/postgis"
)

func main() {
	postgis.Initialize()
	router := http.NewServeMux()
	api := humago.New(router, huma.DefaultConfig("Carputer API", "1.0.0"))

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
			OperationID: "Create Track",
			Method:      http.MethodPost,
			Path:        "/v2/tracks",
			Summary:     "Create Track",
			Description: "Create and starts a track recording. You will be then be able to record track points with the track points endpoint.",
			Tags:        []string{"Tracks"},
		}, handler.CreateTrackHander)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "End Track",
			Method:      http.MethodGet,
			Path:        "/v2/tracks",
			Summary:     "End Track",
			Description: "Ends track recording.",
			Tags:        []string{"Tracks"},
		}, handler.EndTrackHander)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "Add Track Point",
			Method:      http.MethodPost,
			Path:        "/v2/track-point",
			Summary:     "Add Track Point",
			Description: "Adds a track point to the current track that you started.",
			Tags:        []string{"Tracks"},
		}, handler.AddTrackPointHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "List Tracks",
			Method:      http.MethodGet,
			Path:        "/v2/list-tracks",
			Summary:     "List Tracks",
			Description: "List all tracks.",
			Tags:        []string{"Tracks"},
		}, handler.ListTracksHandler)

	huma.Register(
		api,
		huma.Operation{
			OperationID: "Get Track",
			Method:      http.MethodGet,
			Path:        "/v2/track/{track_id}",
			Summary:     "Get Track",
			Description: "Get a track by the track id.",
			Tags:        []string{"Tracks"},
		}, handler.GetTrackHandler)

	fmt.Println("Visit http://127.0.0.1:8000/docs")
	http.ListenAndServe("0.0.0.0:8000", router)
}
