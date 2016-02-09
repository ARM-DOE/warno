from WarnoConfig import utility

db = utility.connect_db()
cur = db.cursor()

# For each entry, first entry is table name, second entry is demo data for the table
table_data = [
                   "users",
                   "sites"
             ]

for table in table_data:
    if utility.table_exists(table, cur):
        utility.load_data_into_table("schema/%s.data" % table, table, db)
