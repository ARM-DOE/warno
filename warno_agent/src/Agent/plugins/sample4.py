import time
import pyarmret
from pyarmret.io.PAFClient import PAFClient


def register():
    event_id = 1
    event_table = None
    event_name = "test_event2"

    return {"event_id": event_id,
            "event_table": event_table,
            "event_name": event_name}


#def run(msg_queue):
    #pafc = PAFClient('brw-kazr', 3000)
    #pafc.connect()
    #pafc.get_server_info()

    #for i in range(0, 10):
    #    try:
    #        msg = pafc.get_server_info()
    #        msg_queue.put(msg)
    #    except Exception, e:
    #        msg_queue.put(e)
    #    else:
    #        pass
    #    finally:
    #        pass

    #    time.sleep(2)
