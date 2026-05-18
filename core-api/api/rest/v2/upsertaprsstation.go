package v2

type UpsertAPRSStationRequest struct {
	Body APRSPacketIn
}

type UpsertAPRSStationResponse struct {
	Body struct {
		Callsign string `json:"callsign"`
	}
}
