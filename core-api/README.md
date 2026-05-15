# Core API
This project is the Core API Project, which aims to facilitate communications across all teams and components in the Carputer project.

## Description
The Core API project aims to replace the old FastAPI service we built during early development. With the concerns of concurrency, speed, efficiency, and limitations of Python and Starlette, we decided to re-write the entire Rest Backend using the Go language, utililizing [Huma](https://huma.rocks/) and [PGX](https://pkg.go.dev/github.com/jackc/pgx/v5).

## Requirements 
- Go version 1.26+

## Development Environment Setup
Navigate to the root of the project  
`$ cd core-api`  

Install dependencies  
`$ go mod tidy`  

That's it! You're ready to develop!

## Running Locally
Ensure your current working directory is in the project's root
```
$ pwd
/home/user/Documents/repo/carputer/core-api
```

Run the go command  
`$ go run cmd/app/main.go`

That's it! You can visit http://localhost:8000/docs to see all the endpoints we got!

## Project Structure
Unlike the previous FastAPI service, we aim to apply industry practices and guidelines in this project. We structured are this go project close to what production-ready Go projects and packages follow.
```
.
└── core-api/
    ├── api/
    │   └── rest/
    │       └── v1/
    ├── cmd/
    │   └── app/
    │       └── main.go
    ├── deployments/
    │   └── docker/
    │       ├── Dockerfile
    │       └── .dockerignore
    ├── internal/
    │   ├── client/
    │   ├── handler/
    │   └── postgis/
    ├── configs/
    │   └── .env.example
    ├── pkg
    ├── go.mod
    ├── go.sum
    ├── .env
    ├── .gitignore
    └── README.md
```


### `/cmd`

This is where your **entry points** live. Each subdirectory under `cmd` represents a separate executable binary.


### `/internal`

This is a special directory in Go. Code inside `/internal` can only be imported by packages within the same parent tree.


### `/pkg`

Unlike `internal`, code in `/pkg` is **public** and can be imported by anyone. This really is only useful if say another go project is importing our project.

**Note:** Since we our Core API is a closed-ecosystem with other carputer services, we might not need this at all.

### `/api`

This folder holds your API contract definitions.

**Examples:** OpenAPI/Swagger specs, JSON schema files, DTOs and Rest Models, etc.

### `/configs`

Configuration file templates or default settings (e.g., `config.yaml`, `.env.example`).

## Authors
Brian Le  
[@ricer0ll](https://github.com/ricer0ll)