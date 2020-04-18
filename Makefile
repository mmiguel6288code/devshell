files = setup.py src/devshell/*.py
all: do_build do_upload do_install
do_build: $(files)
	echo "building"
	if [ -d ./build ]; then rm -rf ./build; fi
	if [ -d ./dist ]; then rm -rf ./dist; fi
	if [ -d ./devshell.egg-info ]; then rm -rf ./devshell.egg-info; fi
	pdoc --html --force --output-dir docs src/devshell
	python3 setup.py sdist bdist_wheel
do_upload: do_build
	echo "uploading"
	python3 -m twine upload dist/*
do_install: do_upload
	echo "installing"
	python3 -m pip install --user --upgrade --force-reinstall devshell
