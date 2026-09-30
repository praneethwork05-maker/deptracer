.PHONY: test install demo clean

install:
	python3 -m pip install -e .

test:
	pytest -q

demo:
	cd examples && pyinstaller --onefile demo_app.py && cd .. && deptracer build examples demo_app examples/demo_app.spec

clean:
	rm -rf .pytest_cache build dist *.egg-info
