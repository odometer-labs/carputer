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
	// Init connection pool
	postgis.Initialize()

	// Configure huma
	var customConfigs huma.Config = huma.DefaultConfig("Carputer API", "1.0.0")
	customConfigs.DocsRenderer = huma.DocsRendererScalar

	// Init router and huma
	router := http.NewServeMux()
	api := humago.New(router, customConfigs)

	// register handlers/endpoints
	utils.RegisterHumaHandlers(api)

	fmt.Println("Visit http://127.0.0.1:8888/docs")
	http.ListenAndServe("0.0.0.0:8888", router)
}
