package v2

type GetVersionHistoryRequest struct{}

type GetVersionHistoryResponse struct {
	Body struct {
		Versions []Version
	}
}
