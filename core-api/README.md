# Core API
This project is the Core API Project, which aims to facilitate communications across all teams and components in the Carputer project.

## Description
The Core API project aims to replace the old FastAPI service we built during early development. With the concerns of concurrency, speed, efficiency, and limitations of Python and Starlette, we decided to re-write the entire Rest Backend using the Go language, utililizing [Huma](https://huma.rocks/) and [PGX](https://pkg.go.dev/github.com/jackc/pgx/v5).

### Requirements 
- Go version 1.26+

### Development Environment Setup
Navigate to the root of the project  
`$ cd core-api`  

Install dependencies  
`$ go mod tidy`  

That's it! You're ready to develop!

### Running Locally
Ensure your current working directory is in the project's root
```
$ pwd
/home/user/Documents/repo/carputer/core-api
```

Run the go command  
`$ go run cmd/app/main.go`

That's it! You can visit http://localhost:8000/docs to see all the endpoints we got!

## Authors
Brian Le  
[@ricer0ll](https://github.com/ricer0ll)