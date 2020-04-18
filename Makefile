files = setup.py src/devshell/*.py
all: do_build do_upload
do_build: $(files)
	echo "building"
	[ -d build ] && rm -rf ./build
	[ -d dist ] && rm -rf ./dist
	python3 setup.py sdist bdist_wheel
do_upload: do_build
	echo "uploading"
	python3 -m twine upload dist/*
