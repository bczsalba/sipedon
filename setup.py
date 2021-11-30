from setuptools import setup, find_packages

setup(
    name="fishtank",
    version="0.0.0",
    include_package_data=True,
    packages=["fishtank"],
    license="MIT",
    description="",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=["pytermgui"],
    python_requires=">=3.7.0",
    url="https://github.com/bczsalba/fishtank",
    author="BcZsalba",
    author_email="bczsalba@gmail.com",
    entry_points={"console_scripts": ["fishtank = fishtank:main"]},
)
