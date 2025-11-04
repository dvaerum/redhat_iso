from setuptools import setup, find_packages

setup(
    name='rhiso',
    version='1.0.0',
    description='Red Hat ISO Download Tool - List and download Red Hat ISO files',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Your Name',
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
    ],
    entry_points={
        'console_scripts': [
            'rhiso=rhiso.cli:main',
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
