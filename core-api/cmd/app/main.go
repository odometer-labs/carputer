package main

import (
	"fmt"
	"net/http"

	"github.com/danielgtaylor/huma/v2"
	"github.com/danielgtaylor/huma/v2/adapters/humago"
	"github.com/odometer-labs/carputer/core-api/internal/postgis"
	"github.com/odometer-labs/carputer/core-api/internal/utils"
)

func main() {
	postgis.Initialize()
	router := http.NewServeMux()
	api := humago.New(router, huma.DefaultConfig("Carputer API", "1.0.0"))

	utils.RegisterHumaHandlers(api)

	fmt.Println("Visit http://127.0.0.1:8000/docs")
	http.ListenAndServe("0.0.0.0:8000", router)
}
