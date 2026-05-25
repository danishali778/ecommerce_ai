PYTHON=python3

.PHONY: api-dev worker beat test compile

api-dev:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd apps/api && celery -A app.core.celery_app.celery_app worker --loglevel=INFO

beat:
	cd apps/api && celery -A app.core.celery_app.celery_app beat --loglevel=INFO

test:
	$(PYTHON) -m pytest apps/api/tests

compile:
	$(PYTHON) -m compileall apps/api/app
