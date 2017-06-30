#!/usr/bin/env bash

if [ "$ANACONDA_HOME" = "" ]; then
    ANACONDA_HOME=/home/vagrant
fi

miniconda=Miniconda-latest-Linux-x86_64.sh
cd $ANACONDA_HOME
if [[ ! -f $miniconda ]]; then
    wget --quiet http://repo.continuum.io/miniconda/$miniconda
fi
chmod +x $miniconda
./$miniconda -b -p $ANACONDA_HOME/anaconda

cat >> $ANACONDA_HOME/.bashrc << END
# Add for install
PATH=$ANACONDA_HOME/anaconda/bin:\$PATH
END

# For remote ssh commands
cat >> $ANACONDA_HOME/.profile << END
# Add for anaconda install
PATH=$ANACONDA_HOME/anaconda/bin:\$PATH
END

export PATH=$ANACONDA_HOME/anaconda/bin:\$PATH

# Current latest versions
# Prevents download of newer versions than are included in included $miniconda
conda install -y psycopg2
conda install -y pandas
conda install -y numpy
conda install -y netcdf4
conda install -y backports
