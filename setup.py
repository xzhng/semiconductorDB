from setuptools import setup, find_packages

setup(
    name="semiconductor_db",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "matplotlib",
        "streamlit"
        # add any other dependencies here
    ],
)
