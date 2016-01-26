import sys


def signal_handler( signal, frame):
    """ Set up Ctrl-C Handling

    This function sets up signal interrupt catching, primarily to handle Ctrl-C.

    Parameters
    ----------
    signal: signal
        Signal to catch
    frame: frame
        frame
    """

    print("Exiting due to SIGINT")
    sys.exit(0)