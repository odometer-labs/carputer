package v2

type GetPositionRequest struct{}

type GetPositionResponse struct {
	Body struct {
		Latitude  float64 `json:"latitude"`
		Longitude float64 `json:"longitude"`
		Speed     float64 `json:"speed"`
		Heading   float64 `json:"heading"`
	}
}
