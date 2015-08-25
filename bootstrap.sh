#!/usr/bin/env bash
miniconda=Miniconda-latest-Linux-x86_64.sh
cd /vagrant
chmod +x $miniconda
./$miniconda -b -p /vagrant/anaconda

cat >> /home/vagrant/.bashrc << END
# add for anaconda install
PATH=/vagrant/anaconda/bin:\$PATH
END

PATH=/vagrant/anaconda/bin:\$PATH

conda install psycopg2
conda install pandas
pip install sqlalchemy
