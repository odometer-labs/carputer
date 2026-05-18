package v2

type GetAPRSStationRequest struct {
	Callsign string `path:"callsign"`
	Body     struct {
		Meters *float64 `json:"meters" default:"500000.0"`
	}
}
