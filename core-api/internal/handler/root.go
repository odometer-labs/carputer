package handler

import (
	"context"

	v2 "github.com/odometer-labs/carputer/core-api/api/rest/v2"
)

func RootHandler(ctx context.Context, request *v2.RootRequest) (*v2.RootResponse, error) {
	resp := &v2.RootResponse{}
	resp.Body.Message = "Hello, World!"
	return resp, nil
}
