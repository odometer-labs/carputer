package v2

type GetTrackPath struct {
	TrackID int64 `path:"track_id"`
}

type GetTrackResponse struct {
	Body Track
}
