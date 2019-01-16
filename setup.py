from setuptools import find_packages, setup

from trench import __version__


setup(
    name='django-trench',
    version=__version__,
    packages=find_packages(exclude=['testproject', 'testproject.*']),
    include_package_data=True,
    license='MIT License',
    description='REST Multi-factor authentication package for Django',
    long_description=open('README.rst').read(),
    long_description_content_type='text/x-rst',
    url='https://github.com/merixstudio/django-trench',
    author='Merixstudio',
    author_email='trench@merixstudio.com',
    install_requires=[
        'pyotp>=2.2.6',
        'twilio>=6.18.1',
        'yubico-client>=1.10.0',
        'smsapi-client>=2.2.5',
    ],
    classifiers=[
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
