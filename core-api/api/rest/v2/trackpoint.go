package v2

type TrackPoint struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	Speed     float64 `json:"speed"`
	Heading   float64 `json:"heading"`
}

type AddTrackPointRequest struct {
	Body TrackPoint
}

type AddTrackPointResponse struct{}
