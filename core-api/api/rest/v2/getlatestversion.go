package v2

type GetLatestVersionRequest struct{}

type GetLatestVersionResponse struct {
	Body struct {
		ID      uint64 `json:"id"`
		Version Version
	}
}
