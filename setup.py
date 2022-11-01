from setuptools import setup, find_packages

with open('README.rst') as f:
    long_description = ''.join(f.readlines())

setup(
    name='committee_ancinpet',
    version='0.5.4',
    description='Github Commit Checker',
    long_description=long_description,
    author='Petr Ančinec',
    author_email='ancinpet@fit.cvut.cz',
    keywords='github,click,git,flask,commits',
    license='MIT License',
    url='https://github.com/fitancinpet/committee',
    packages=find_packages(include=['committee', 'committee.*']),
    install_requires=['Flask', 'click>=6', 'requests'],
    python_requires='>=3.6',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Framework :: Flask',
        'Environment :: Web Environment',
        'Environment :: Console',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft',
        'Topic :: Software Development :: Libraries'
    ],
    entry_points={
        'console_scripts': [
            'committee=committee.committee:main',
        ],
    },
    zip_safe=False,
    package_data={'committee': ['templates/*.html']},
)
