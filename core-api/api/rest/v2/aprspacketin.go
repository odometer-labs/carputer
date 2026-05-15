package v2

type APRSPacketIn struct {
	Callsign    string   `json:"callsign"`
	Latitude    *float64 `json:"latitude"`
	Longitude   *float64 `json:"longitude"`
	SymbolTable string   `json:"symbol_table"`
	SymbolCode  string   `json:"symbol_code"`
	Comment     string   `json:"comment"`
	AltitudeM   *float64 `json:"altitude_m"`
	SpeedKnots  *float64 `json:"speed_knots"`
	CourseDeg   *float64 `json:"course_deg"`
	RawPacket   string   `json:"raw_packet"`
}
