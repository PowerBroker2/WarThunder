from setuptools import setup

setup(
    name             = 'WarThunder',
    packages         = ['WarThunder'],
    version          = '2.1.12',
    description      = 'Python package used to access air vehicle telemetry while in War Thunder air battles',
    author           = 'Power_Broker',
    author_email     = 'gitstuff2@gmail.com',
    url              = 'https://github.com/PowerBroker2/WarThunder',
    download_url     = 'https://github.com/PowerBroker2/WarThunder/archive/2.1.12.tar.gz',
    keywords         = ['War Thunder'],
    classifiers      = [],
    install_requires = ['imagehash', 'requests', 'Pillow', 'WarThunder']
)
