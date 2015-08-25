import utility

db = utility.connect_db()
cur = db.cursor()

utility.initialize_database(cur)
db.commit()

# For each entry, first entry is table name, second entry is demo data for the table
table_data = [
                   ["users", "users.data"],
                   ["sites", "sites.data"],
                   ["instruments", "instruments.data"],
                   ["instrument_logs", "logs.data"],
                   ["prosensing_paf", "prosensing_paf.data"]
               ]

for table in table_data:
    if utility.table_exists(table[0], cur):
        utility.load_data_into_table("schema/%s" % table[1], table[0], db)
