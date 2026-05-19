package v2

type CreateTrackRequest struct {
	Body struct {
		TrackName *string `json:"track_name"`
	}
}

type CreateTrackResponse struct {
	Body struct {
		ID int64 `json:"id"`
	}
}
