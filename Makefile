PROJECT_NAME ?= backendschool2022
VERSION = $(shell python3 setup.py --version | tr '+' '-')
PROJECT_NAMESPACE ?= kernie
REGISTRY_IMAGE ?= $(PROJECT_NAMESPACE)/$(PROJECT_NAME)

all:
	@echo "make devenv		- Create & setup development virtual environment"
	@echo "make lint		- Check code with pylama"
	@echo "make postgres	- Start postgres container"
	@echo "make clean		- Remove files created by distutils"
	@echo "make test		- Run tests"
	@echo "make sdist		- Make source distribution"
	@echo "make docker		- Build a docker image"
	@echo "make upload		- Upload docker image to the registry"
	@exit 0

clean:
	rm -fr *.egg-info dist

devenv: clean
	rm -rf env
	# создаем новое окружение
	python3.10 -m venv env
	# обновляем pip
	env/bin/pip install -U pip
	# устанавливаем основные + dev зависимости из extras_require (см. setup.py)
	env/bin/pip install -Ue '.[dev]'

lint:
	env/bin/pylama

postgres:
	docker stop market-postgres || true
	docker run --rm --detach --name=market-postgres \
		--env POSTGRES_USER=user \
		--env POSTGRES_PASSWORD=hackme \
		--env POSTGRES_DB=market \
		--publish 5432:5432 postgres

test:
	cd tests && ../env/bin/python3 -m unit_tests http://127.0.0.1:80

sdist: clean
	# официальный способ дистрибуции python-модулей
	python3 setup.py sdist

docker: sdist
	docker build -t $(PROJECT_NAME):$(VERSION) .

upload: docker
	docker tag $(PROJECT_NAME):$(VERSION) $(REGISTRY_IMAGE):$(VERSION)
	docker tag $(PROJECT_NAME):$(VERSION) $(REGISTRY_IMAGE):latest
	docker push $(REGISTRY_IMAGE):$(VERSION)
	docker push $(REGISTRY_IMAGE):latest
