package v2

type DeleteRegionRequest struct {
	Body struct {
		Id uint64 `json:"id"`
	}
}

type DeleteRegionResponse struct{}
