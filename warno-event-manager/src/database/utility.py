import psycopg2
import numpy as np

def table_exists(table_name, curr):
    SQL = "SELECT relname FROM pg_class WHERE relname = %s;"
    curr.execute(SQL, (table_name,))
    if curr.fetchone() == None:
        return False
    else:
        return True

def drop_table(table_name, curr):
    SQL = "DROP TABLE IF EXISTS %s;"
    #try:
    curr.execute(SQL, (table_name,))
    #except Exception as e:
    #    print("Table Does not Exist")



def create_table_from_file(filename, curr):
    f = open(filename)
    try:
        curr.execute(f.read())
    except Exception as e:
        print("Table Already exists")


def insert_test_data(curr, month=1):
    SQL =  "INSERT INTO usage(time,server,site,cpu_usage_user,cpu_usage_system,virtual_usage_percent,swap_usage_percent,storage_used) VALUES ('2015-%s-%s %s:%s:00',E'kazr2',E'ENA',%s,%s,%s,%s,%s);"
    for day in np.arange(1,29):
        for hour in np.arange(0,23):
            for minute in np.arange(0,59):
                curr.execute(SQL,(month,day,hour,minute,day+minute/10.0, day+hour/20.0,hour +2/day, day+minute, day*minute/7.2))

    
