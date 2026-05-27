package v2

type RegionDataModel struct {
	Id   uint64  `json:"id"`
	MinX float64 `json:"min_x"`
	MaxX float64 `json:"max_x"`
	MinY float64 `json:"min_y"`
	MaxY float64 `json:"max_y"`
	Name string  `json:"name"`
}

type ListRegionsRequest struct{}

type ListRegionsResponse struct {
	Body struct {
		Regions []RegionDataModel `json:"regions"`
	}
}
