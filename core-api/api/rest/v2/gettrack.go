package v2

type GetTrackPath struct {
	TrackID uint64 `path:"track_id"`
}

type GetTrackResponse struct {
	Body Track
}
