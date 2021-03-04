from setuptools import find_packages, setup

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='fxy',
    version='0.1.7',
    description='Convenience imports and scientific functions.',
    long_description=long_description,
    url='https://github.com/mindey/fxy',
    author='Mindey',
    author_email='mindey@qq.com',
    license='UNLICENSE',
    packages = find_packages(exclude=['docs', 'tests*']),
    install_requires=[],
    extras_require = {
        'test': ['coverage', 'pytest', 'pytest-cov'],
        'main': ["sympy", "xarray", "scipy", "statsmodels", "sklearn", "matplotlib", "seaborn"],
        'all': ["sympy", "xarray", "scipy", "statsmodels", "sklearn", "matplotlib", "seaborn"] + ["xgboost"]
    },
    zip_safe=False
)
