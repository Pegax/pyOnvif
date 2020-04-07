pyOnvif
=======

This package provides a simple client to interact with ONVIF compliant IP cameras. It contains the SOAP message encoding for the basic functions that are commonly needed.

There are no required dependencies. Optionally, if you want to use WS-Discovery to find your Onvif camera, you need `WS-Discovery support <https://pypi.python.org/pypi/WSDiscovery>`_.

WS-Discovery support can also be installed by including the 'discovery' extra, as in::

    pip install pyonvif[discovery]

For command-line usage instructions run:

    pyonvif -h
