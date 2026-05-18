package v2

type GetAPRSStationsNearRequest struct {
	Body struct {
		Meters *float64 `json:"meters" default:"500000.0"`
	}
}

type GetAPRSStationsNearResponse struct {
	Body struct {
		APRSStations []APRSStation `json:"aprs_stations"`
	}
}
