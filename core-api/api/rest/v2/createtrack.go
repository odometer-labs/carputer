package v2

import "time"

type CreateTrackRequest struct {
	Body struct {
		StartTime time.Time `json:"start_time"`
		EndTime   time.Time `json:"end_time"`
		TrackName *string   `json:"track_name"`
	}
}

type CreateTrackResponse struct {
	Body struct {
		ID int64 `json:"id"`
	}
}
