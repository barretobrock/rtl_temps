
bump-patch:
	sh ppmgr.sh bump
bump-minor:
	sh ppmgr.sh bump minor
bump-major:
	sh ppmgr.sh bump major
pull:
	sh ppmgr.sh pull
push:
	sh ppmgr.sh push
debug-run:
	python3 run_debug.py
check:
	pre-commit run --all-files
install:
	# First-time install - use when lock file is stable
	poetry install -v
update:
	# Update lock file based on changed reqs
	poetry update -v

test:
	tox
rebuild-test:
	tox --recreate -e py310
