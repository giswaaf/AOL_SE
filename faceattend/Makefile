.PHONY: dev prod stop clean logs

dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

stop:
	docker-compose down

clean:
	docker-compose down -v

logs:
	docker-compose logs -f

build:
	docker-compose build
