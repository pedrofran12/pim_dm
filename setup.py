import sys
from setuptools import setup, find_packages

# we only support Python 3 version >= 3.3
if len(sys.argv) >= 2 and sys.argv[1] == "install" and sys.version_info < (3, 3):
    raise SystemExit("Python 3.3 or higher is required")


setup(
    name="pim-dm",
    description="PIM-DM protocol",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    keywords="PIM-DM Multicast Routing Protocol PIM Dense-Mode Router RFC3973 IPv4 IPv6",
    version="1.3.5",
    url="http://github.com/pedrofran12/pim_dm",
    author="Pedro Oliveira",
    author_email="pedro.francisco.oliveira@tecnico.ulisboa.pt",
    license="MIT",
    install_requires=[
        'PrettyTable',
        'netifaces',
        'ipaddress',
        'pyroute2',
        'py-mld==1.0.2',
        'igmp==1.0.2',
    ],
    packages=find_packages(exclude=["docs"]),
    entry_points={
        "console_scripts": [
            "pim-dm = pimdm.Run:main",
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
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.3",
)
