package v2

import (
	"encoding/json"
	"time"
)

type Track struct {
	TrackID   int64           `json:"track_id"`
	Geom      json.RawMessage `json:"geom"`
	GeomWM    json.RawMessage `json:"geom_wm"`
	StartTime time.Time       `json:"start_time"`
	EndTime   time.Time       `json:"end_time"`
	TrackName *string         `json:"track_name"`
}
