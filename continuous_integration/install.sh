#!/bin/bash
# This script was adpated from the pyart install.sh script.
# This script is adapted from the install.sh script from the scikit-learn
# project: https://github.com/scikit-learn/scikit-learn

# This script is meant to be called by the "install" step defined in
# .travis.yml. See http://docs.travis-ci.com/ for more details.
# The behavior of the script is controlled by environment variabled defined
# in the .travis.yml in the top level folder of the project.

set -e
# use next line to debug this script
#set -x

# Use Miniconda to provide a Python environment.  This allows us to perform
# a conda based install of the SciPy stack on multiple versions of Python
# as well as use conda and binstar to install additional modules which are not
# in the default repository.
wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh \
    -O miniconda.sh
chmod +x miniconda.sh
./miniconda.sh -b
export PATH=/home/jenkins/anaconda/bin:$PATH
conda update --yes conda


# Create a testenv with the correct Python version
conda create -n testenv --yes pip python=2.7
source activate testenv


# Install dependencies
conda install --yes numpy nose netcdf4 psycopg2 pandas

pip install pyyaml Flask requests selenium nose-cov nose-exclude mock sqlalchemy flask-testing blinker

git clone http://overwatch.pnl.gov/hard505/pypro-aflib.git
cd pypro-aflib
python setup.py install
cd ..

# install coverage modules
source utility_setup_scripts/set_env_for_testing.sh