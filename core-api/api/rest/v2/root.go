package v2

type RootResponse struct {
	Body struct {
		Message string `json:"message"`
	}
}

type RootRequest struct{}
