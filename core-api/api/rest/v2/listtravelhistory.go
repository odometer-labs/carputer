package v2

type TravelHistoryResponse struct {
	ID int64 `json:"id"`
	TravelHistory
}

type ListTravelHistoryRequest struct {
}

type ListTravelHistoryResponse struct {
	Body struct {
		TravelHistory []TravelHistoryResponse
	}
}
