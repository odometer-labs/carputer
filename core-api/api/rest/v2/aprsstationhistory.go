package v2

import "time"

type APRSStationHistory struct {
	TimeStamp  time.Time `json:"time_stamp"`
	Latitude   float64   `json:"latitude"`
	Longitude  float64   `json:"longitude"`
	AltitudeM  *float64  `json:"altitude_m"`
	SpeedKnots *float64  `json:"speed_knots"`
	CourseDeg  *float64  `json:"course_deg"`
	Comment    *string   `json:"comment"`
}
