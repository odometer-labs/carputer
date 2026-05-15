package v1

import "time"

type StartTrackRequest struct {
	Body struct {
		StartTime time.Time `json:"start_time"`
		EndTime   time.Time `json:"end_time"`
		TrackName *string   `json:"track_name"`
	}
}

type StartTrackResponse struct {
	Body struct {
		ID int64 `json:"id"`
	}
}
