import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


# we only support Python 3 version >= 3.4
#if len(sys.argv) >= 2 and sys.argv[1] == "install" and sys.version_info < (3, 4):
#    raise SystemExit("Python 3.4 or higher is required")


dependencies = open("requirements.txt", "r").read().splitlines()

setup(
    name="pim-dm",
    version="1.0",
    url="http://github.com/pedrofran12/pim_dm",
    license="MIT",
    description="PIM-DM protocol",
    long_description=open("README.md", "r").read(),
    install_requires=dependencies,
    packages=find_packages(exclude=["docs"]),
    py_modules=["Run", "Interface", "InterfaceIGMP", "InterfacePIM", "Kernel", "Main", "Neighbor",
                "TestLogger", "UnicastRouting", "utils"],
    entry_points={
        "console_scripts": [
            "pim-dm = Run:main",
        ]
    },
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
)
