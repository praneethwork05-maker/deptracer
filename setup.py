from setuptools import setup, find_packages

setup(
    name="deptracer-tathack",
    version="0.2.0",
    description="Runtime dependency discovery and PyInstaller spec automation",
    packages=find_packages(),
    entry_points={"console_scripts": ["deptracer=deptracer.cli:main"]},
    python_requires=">=3.8",
)
