package v2

type ListTracksMVTRequest struct {
	TrackID int64 `path:"track_id"`
	Body    struct {
		X            int64   `json:"x"`
		Y            int64   `json:"y"`
		Z            int64   `json:"z"`
		Mode         string  `json:"mode" default:"all"`
		WithinMeters float64 `json:"within_meters"`
	}
}

type ListTracksMVTResponse struct {
	Body struct {
		Bytes []byte `json:"bytes"`
	}
}
