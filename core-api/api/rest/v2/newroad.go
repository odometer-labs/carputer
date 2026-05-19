package v2

type CheckNewRoadRequest struct{}

type CheckNewRoadResponse struct {
	Body struct {
		IsNewRoad bool `json:"is_new_road"`
	}
}
