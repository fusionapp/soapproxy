from setuptools import find_packages, setup
setup(
    name='soapproxy',
    version='0.0.1',
    maintainer='Fusion Dealership Systems',
    description='A simple SOAP reverse proxy thing.',
    url='https://github.com/fusionapp/soapproxy',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    packages=find_packages() + ['twisted.plugins'],
    install_requires=[
        'Twisted[tls] >= 15.0.0',
        'lxml>=3.6.0',
    ])
