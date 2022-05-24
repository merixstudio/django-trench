from setuptools import find_packages, setup

from trench import __version__


setup(
    name="django-trench",
    version=__version__,
    packages=find_packages(exclude=("testproject", "testproject.*")),
    include_package_data=True,
    license="MIT License",
    description="REST Multi-factor authentication package for Django",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    url="https://github.com/merixstudio/django-trench",
    author="Merixstudio",
    author_email="trench@merixstudio.com",
    install_requires=[
        "pyotp>=2.6.0",
        "twilio>=6.56.0",
        "yubico-client>=1.13.0",
        "smsapi-client>=2.4.5",
    ],
    extras_require={
        'docs': [
            'sphinx >= 1.4',
            'sphinx_rtd_theme',
        ]
    },
    classifiers=[
        "Framework :: Django",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
