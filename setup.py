from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='acm_report',
    packages=['acm_report'],
    include_package_data=True,
    install_requires=required,
)
