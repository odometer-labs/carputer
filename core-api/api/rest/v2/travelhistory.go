package v2

import "time"

type CreateTravelHistoryBody struct {
	MinX    float64 `json:"min_x"`
	MaxX    float64 `json:"max_x"`
	MinY    float64 `json:"min_y"`
	MaxY    float64 `json:"max_y"`
	TrackID int64   `json:"track_id"`
}

type TravelHistory struct {
	CreateTravelHistoryBody
	CreatedAt time.Time `json:"created_at"`
}
