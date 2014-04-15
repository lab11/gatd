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

```python
class yourParser (parser):
  def __init__():
    # you can create any state or whatnot



  # parse() gets called for each incoming packet.
  #
  # data  :    The raw string from the packet sent to the receiver.
  # meta  :    Extra data related to the packet being parsed.
  #            type: dict
  #             ['addr'] = ipv6 address of the sender
  #             ['port'] = port of the sender socket
  #             ['time'] = unix timestamp of when the receiver received the packet
  # extra :    Static data associated with this parser/data source.
  # settings : Currently blank.
  #
  # return : This function must return a dict. The key, value pairs will be stored
  #          in the database as key value pairs.
  def parse (self, data, meta, extra, settings):
```
