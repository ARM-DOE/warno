#!/usr/bin/env bash
miniconda=Miniconda-latest-Linux-x86_64.sh
cd /home/vagrant
if [[ ! -f $miniconda ]]; then
    wget --quiet http://repo.continuum.io/miniconda/$miniconda
fi
chmod +x $miniconda
./$miniconda -b -p /home/vagrant/anaconda

cat >> /home/vagrant/.bashrc << END
# Add for install
PATH=/home/vagrant/anaconda/bin:\$PATH
END

# For remote ssh commands
cat >> /home/vagrant/.profile << END
# Add for anaconda install
PATH=/home/vagrant/anaconda/bin:\$PATH
END

export PATH=/home/vagrant/anaconda/bin:\$PATH

# Current latest versions
# Prevents download of newer versions than are included in included $miniconda
conda install -y psycopg2
conda install -y pandas
conda install -y numpy
conda install -y netcdf4
