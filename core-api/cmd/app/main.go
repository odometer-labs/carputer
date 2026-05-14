package main

import (
	"fmt"
	"net/http"

	"github.com/danielgtaylor/huma/v2"
	"github.com/danielgtaylor/huma/v2/adapters/humago"
	"github.com/odometer-labs/carputer/core-api/internal/handler"
)

func main() {
	router := http.NewServeMux()
	api := humago.New(router, huma.DefaultConfig("Carputer API", "1.0.0"))

	huma.Get(
		api,
		"/v1/root",
		handler.RootHandler,
	)

	fmt.Println("Visit http://127.0.0.1:8888/docs")
	http.ListenAndServe("127.0.0.1:8888", router)
}
