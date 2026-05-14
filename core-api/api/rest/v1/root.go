package v1

type RootResponse struct {
	Body struct {
		Message string `json:"message"`
	}
}

type RootRequest struct{}
