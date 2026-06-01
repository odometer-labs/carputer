package v2

import "time"

type GetLatestTrackPointRequest struct{}

type LatestTrackPoint struct {
	PointID    int64     `json:"point_id"`
	TrackID    int64     `json:"track_id"`
	TimeStamp  time.Time `json:"time_stamp"`
	Geom       string    `json:"geom"`
	SpeedMPS   float64   `json:"speed_mps"`
	HeadingDeg float64   `json:"heading_deg"`
}

type GetLatestTrackPointResponse struct {
	Body LatestTrackPoint
}
