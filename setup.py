from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

setup(
    name="internet-curator",
    version="0.0.1",
    description="Internet curator",
    long_description=readme,
    author="Rolv-Arild Braaten, Aksel Hjerpbakk",
    author_email="rolv.braaten@nb.no, aksel.hjerpbakk@nb.no",
    url="https://github.com/Rolv-Arild/nb-internet-curator",
    packages=find_packages(include="src")
)
