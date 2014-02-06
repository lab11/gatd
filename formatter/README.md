Formatter Service
=================

This service processes the raw incoming packets into (key,value) pairs that
are streamed to clients and stored in a database.


Formatters
----------

Formatters are python classes that take in the raw incoming
data, process it, and return (key, value) pairs that are streamed and stored.

### Python formatter

Each formatter must be a class like the following:

```
class yourParser (parser):
  def __init__():
    # you can create any state or whatnot



  # parse() get's called for each incoming packet.
  #
  # data  :    The raw string from the packet sent to the receiver.
  # meta  :    Extra data related to the packet being parsed.
  #            type: dict
  #             ['addr'] = ipv6 address of the sender
  #             ['port'] = port of the sender socket
  #             ['time'] = unix timestamp of when the receiver received the packet
  # extra :    Static data associated with this parser/data source. This data is loaded
  #            beforehand with this parser. An example of where this would be useful
  #            is with location data. In theory the location of a sensor is known
  #            ahead of time and the parser can then add it to the record so the
  #            location is set in the database.
  # settings : This dictionary contains the settings info from the config file.
  #
  # return : This function must return a dict. The key, value pairs will be stored
  #          in the database as key value pairs.
  def parse (self, data, meta, extra, settings):
```
