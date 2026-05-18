package v2

type ImportTrackRequest struct {
	Body struct {
		GeoJSONData string `json:"geojson_data"`
	}
}

type ImportTrackResponse struct {
	Body struct {
		ID int64 `json:"id"`
	}
}
