files = setup.py doctestify/*.py
all: build upload
build: $(files)
	echo "building"
	[ -d "./build" ] && rm -rf ./build
	[ -d "./dist" ] && rm -rf ./dist
	python3 setup.py sdist bdist_wheel
upload: build
	echo "uploading"
	python3 -m twine upload dist/*
