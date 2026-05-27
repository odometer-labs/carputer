package v2

type ListRegionsRequest struct{}

type ListRegionsResponse struct {
	Body struct {
		Regions []Region `json:"regions"`
	}
}
