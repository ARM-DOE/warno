import utility

db = utility.connect_db()
cur = db.cursor()

# For each entry, first entry is table name, second entry is demo data for the table
table_data = [
                   ["instruments", "instruments.data"],
                   ["instrument_logs", "logs.data"],
                   ["prosensing_paf", "prosensing_paf.data"],
                   ["event_codes", "event_codes.data"],
                   ["events_with_text", "events_with_text.data"],
                   ["events_with_value", "events_with_value.data"],
                   ["pulse_captures", "pulse_captures.data"],
                   ["table_references", "table_references.data"],
                   ["instrument_data_references", "instrument_data_references.data"]
               ]

for table in table_data:
    if utility.table_exists(table[0], cur):
        utility.load_data_into_table("schema/%s" % table[1], table[0], db)
