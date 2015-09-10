#!/usr/bin/env bash
miniconda=Miniconda-latest-Linux-x86_64.sh
cd /vagrant
if [[ ! -f $miniconda ]]; then
    wget --quiet http://repo.continuum.io/miniconda/$miniconda
fi
chmod +x $miniconda
./$miniconda -b -p /vagrant/anaconda

cat >> /home/vagrant/.bashrc << END
# Add for anaconda install
PATH=/vagrant/anaconda/bin:\$PATH
END

PATH=/vagrant/anaconda/bin:\$PATH

# Current latest versions
# Prevents download of newer versions than are included in included $miniconda
conda install psycopg2=2.6
conda install pandas=0.16.2
pip install sqlalchemy==1.0.8
