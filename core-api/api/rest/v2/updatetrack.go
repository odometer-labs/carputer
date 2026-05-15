package v2

type UpdateTrackRequest struct {
	TrackID int64 `path:"track_id"`
	Body    Track
}

type UpdateTrackResponse struct{}
