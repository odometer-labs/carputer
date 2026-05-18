package v2

type CleanUpOldDataRequest struct {
	Body struct {
		HistoryDays int `json:"history_days" default:"30"`
		RawDays     int `json:"raw_days" default:"7"`
	}
}

type CleanupOldDataResponse struct{}
