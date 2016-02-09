
EVENT_CODE_REQUEST = 1
SITE_ID_REQUEST = 2
INSTRUMENT_ID_REQUEST = 3
PULSE_CAPTURE = 4
PROSENSING_PAF = 5

status_text = {1: "OPERATIONAL",
               2: "NOT WORKING",
               3: "TESTING",
               4: "IN-UPGRADE",
               5: "TRANSIT"}


def status_code_to_text(status):
    """Convert an instrument's status code to its text equivalent.
    TODO: Refactor this out to utility.
    Parameters
    ----------
    status: integer
        The status code to be converted.

    Returns
    -------
    status_text: string
        Returns a string representation of the status code from the status_text dictionary.
    """
    return status_text[int(status)]