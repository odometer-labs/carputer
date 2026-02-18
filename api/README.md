# API

This project is a shared API built with FastAPI, offering HTTP and WebSocket endpoints for accessing a PostgreSQL database.

## Description

As stated, we are using FastAPI to quickly scale up and deliver necessary endpoints for other services and teams to utilize. We offer HTTP endpoints 
which is recommended for frontend services and a websocket server which is recommended for any application needing real-time communication.  

Should any feature or endpoints is needed by any team, they may request the backend team to create these endpoints.  

Documentations about FastAPI can be found here: https://fastapi.tiangolo.com/

## Getting Started

### Requirements

* [uv Package Manager](https://docs.astral.sh/uv/)

### Setting up development environment
Install uv if you haven't already: https://docs.astral.sh/uv/getting-started/installation/  

Navigate to this project's root:  
`cd api`

Create virtual environment with uv:  
`uv venv --python 3.13`

Activate virtual environment.  
macOS and Linux: `source .venv/bin/activate`  
Windows: `.venv\Scripts\activate`  

Install python packages:  
`uv pip install -r requirements.txt`  

### Starting the server

Running locally:
`fastapi dev ./src/main.py`

### Running Tests
Before running pytest, be sure that you start the server locally (see above). 
Otherwise, the tests will fail. 

Running pytest:  
`pytest`

## Authors
Brian Le  
[@ricer0ll](https://github.com/ricer0ll)

Alan Ho  
[@alan-ho16](https://github.com/alan-ho16)