#
# python3 build.py sdist bdist_wheel  # Command to build the package
# pip3 install dist/*.whl             # Command to install the built package
#

from setuptools import setup, find_packages

setup(
    name='limxsdk',  # Package name
    version='3.4.0',  # Package version
    packages=find_packages(include=['limxsdk', 'limxsdk.*']),  # Include 'limxsdk' and subpackages
    package_dir={'': '.'},  # Root directory is current directory
    include_package_data=True,  # Include additional files specified in MANIFEST.in
    package_data={
        '': ['*.py', '*.so*', '*.lib', '*.pyd'],  # Include these file types
    },
    install_requires=[
        'onnxruntime',
        'pyyaml',
        'numpy>1.21.0,<1.26.4',
        'pygame',
        'scipy',
        'pandas',
        'mujoco==3.2.2',
    ],
)
