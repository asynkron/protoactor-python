import re

from setuptools import setup


def get_version():
    init_py = open('protoactor/__init__.py').read()
    # TODO: make this work with both single and double quotes
    metadata = dict(re.findall("__([a-z]+)__ = \"([^\"]+)\"", init_py))
    return metadata['version']


setup(
    name="ProtoActor Python",
    version=get_version(),
    license="Apache License 2.0",
    description="Protocol buffers & actors",
    long_description="",
    packages=["protoactor"],
    package_dir={"protoactor": "protoactor"},
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
