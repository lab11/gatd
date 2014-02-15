GATD - Processors
=================

Processors take formatted data and apply some transformation to it. In contrast
to formatters, processors can be stateful and complex if needed.
Each processor binds to the queue coming out of the formatter, takes any packets
it needs to process, generates any new packets, and sends the new packets
back to the formatter. The formatter then puts the new packets in the database
and puts the processed packets back in the queue. In this way, packets could
be processed many times.

Processor Keys
--------------

There are special set of keys that identify which identify which processors
a packet has gone through. All of these keys begin with `_processor`.

Each packet has a count of the number of processors it has gone through.
When a packet leaves the formatter it has the key `_processor_count` with the
value `0`. This is incremented after each processor.

Each processor also adds a key named `_processor_<processor name>`. The value
of this key is either `last`, to signify that it was the most recent processor
on this packet, or a zero-indexed integer signifying the order in which the
processor operated on the packet.

### Example

If a packet has been through three processors, named "downsample", "smooth",
and "parametrize", the packet after leaving the parametrize processor would
look like:

    {'profile_id': 'xxx',
     '_processor_count': 3,
     '_processor_downsample': 0,
     '_processor_smooth': 1,
     '_processor_parametrize': 'last',
     <all other keys>
    }
