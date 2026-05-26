package v2

import "time"

type TravelHistory struct {
	MinX      float64   `json:"min_x"`
	MaxX      float64   `json:"max_x"`
	MinY      float64   `json:"min_y"`
	MaxY      float64   `json:"max_y"`
	TrackID   uint64    `json:"track_id"`
	CreatedAt time.Time `json:"created_at" required:"false"`
}
