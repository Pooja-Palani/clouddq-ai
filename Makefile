.PHONY: local-api local-web build-frontend sam-build sam-deploy

local-api:
	cd backend && python3 local_server.py

local-web:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

sam-build:
	cd backend && sam build

sam-deploy:
	cd backend && sam deploy
