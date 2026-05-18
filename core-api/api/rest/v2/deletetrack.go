package v2

type DeleteTrackRequest struct {
	TrackID uint64 `path:"track_id"`
}

type DeleteTrackResponse struct{}
