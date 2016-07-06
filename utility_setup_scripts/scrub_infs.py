import sqlalchemy

engine = sqlalchemy.create_engine('postgresql://warno:warno@192.168.50.100:5432/warno')
conn = engine.connect()
result = conn.execute("select column_name,data_type from information_schema.columns where table_name = 'prosensing_paf'")
keys = [row[0] for row in result if row[1] in ["double precision"]]
for key in keys:
    print conn.execute("update prosensing_paf set %s = NULL where %s = '-Infinity' or %s = 'Infinity'" % (key, key, key))

conn.execute("COMMIT")
conn.close()
