package v2

type GetAPRSStationHistoryRequest struct {
	Body struct {
		Callsign string `json:"callsign"`
		Hours    int    `json:"hours"`
	}
}

type GetAPRSStationHistoryResponse struct {
	Body struct {
		APRSStationHistory []APRSStationHistory `json:"aprs_station_history"`
	}
}
