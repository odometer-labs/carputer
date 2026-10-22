package v2

type UpdateTrackRequest struct {
	TrackID uint64 `path:"track_id"`
	Body    Track
}

type UpdateTrackResponse struct{}
