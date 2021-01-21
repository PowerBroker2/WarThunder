from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name             = 'WarThunder',
    packages         = ['WarThunder'],
    version          = '2.2.2',
    description      = 'Python package used to access air vehicle telemetry while in War Thunder air battles',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    author           = 'Power_Broker',
    author_email     = 'gitstuff2@gmail.com',
    url              = 'https://github.com/PowerBroker2/WarThunder',
    download_url     = 'https://github.com/PowerBroker2/WarThunder/archive/2.2.2.tar.gz',
    keywords         = ['War Thunder'],
    classifiers      = [],
    install_requires = ['imagehash', 'requests', 'Pillow', 'WarThunder']
)
