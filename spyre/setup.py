from setuptools import setup

setup(
    name="Spyre",
    version="0.1.0",
    author="Kevin Miao",
    author_email="kcmiao@gmail.com",
    description="Scientific Python Research Environment",
    packages=['spyre',],
    install_requires=[
        'numpy>=1.10.4',
        'scipy>=0.16.0',
        'pandas>=0.19.2',
        'lantz',
        'pint>=0.7.2',
        'pyqtgraph>=0.10.0',
        'pyyaml>=3.11',
        'qtconsole',
        # 'pyqt>=5.6.0',
    ],
    entry_points={
        'gui_scripts': [
            'spyre = spyre.__main__:main',
        ],
    },
)
