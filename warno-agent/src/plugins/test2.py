import time

def register(msg_queue):
    event_code_names = ["temperature", "zenith", "voltage", "sidelobe", "central"]
    instrument_name = "SACR-2"

    # for e_type in event_types:
    #     print "Requesting Event code"
    #     msg_queue.put('{"Event_Code": 1, "Data": "%s"}' % e_type)
    return {"instrument_name": instrument_name, "event_code_names": event_code_names}


def run(msg_queue, instrument_id):
    i = 0
    while True:
        i = i + 1
        timestamp = time.mktime(time.localtime())
        msg_queue.put('{"event": "temperature", "data": {"Instrument_Id": %s, "Time": %s, "Value": "%s"}}' % (instrument_id, timestamp, i))
        msg_queue.put('{"event": "zenith", "data": {"Instrument_Id": %s, "Time": %s, "Value": "%s"}}' % (instrument_id, timestamp, i))
        msg_queue.put('{"event": "voltage", "data": {"Instrument_Id": %s, "Time": %s, "Value": "%s"}}' % (instrument_id, timestamp, i))
        msg_queue.put('{"event": "sidelobe", "data": {"Instrument_Id": %s, "Time": %s, "Value": "%s"}}' % (instrument_id, timestamp, i))
        msg_queue.put('{"event": "central", "data": {"Instrument_Id": %s, "Time": %s, "Value": "%s"}}' % (instrument_id, timestamp, i))
        time.sleep(5)
        # msg_queue.put('{"Tick": %i}' % i)
        # time.sleep(6)
        # pafc = PAFClient('ena-kazr', 3000)
        # pafc.connect()
        # timestamp = time.mktime(time.localtime())
        # if i < 4:
        #     print("Sending Value")
        #     msg_queue.put('{"Event_Code": 4, "Data": {"Instrument_Id": 1, "Time": %s, "Value": %s}}' % (timestamp, i))
