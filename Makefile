files = setup.py src/devshell/*.py
all: do_build do_upload
do_build: $(files)
	echo "building"
	if [ -d ./build ]; then rm -rf ./build; fi
	if [ -d ./dist ]; then rm -rf ./dist; fi
	python3 setup.py sdist bdist_wheel
do_upload: do_build
	echo "uploading"
	python3 -m twine upload dist/*
