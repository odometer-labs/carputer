package handler

import (
	"context"

	v1 "github.com/odometer-labs/carputer/core-api/api/rest/v1"
)

func RootHandler(ctx context.Context, request *v1.RootRequest) (*v1.RootResponse, error) {
	resp := &v1.RootResponse{}
	resp.Body.Message = "Hello, World!"
	return resp, nil
}
