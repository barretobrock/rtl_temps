home := /home/bobrock
pyvenv := $(home)/venvs/rtl_temps/bin/python3

bump-patch:
	sh ppmgr.sh bump
bump-minor:
	sh ppmgr.sh bump minor
bump-major:
	sh ppmgr.sh bump major
pull:
	git pull origin main
	install
push:
	git push origin main
install:
	$(pyvenv) -m pip install -r requirements.txt
update:
	$(pyvenv) -m pip install -r requirements.txt --upgrade

test:
	tox
rebuild-test:
	tox --recreate -e py310
