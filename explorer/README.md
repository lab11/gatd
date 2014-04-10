Explorer
========

The explorer module allows for discovery of various device-level data streams
inside of a particular profile. Each profile author must identify which keys
identify interesting streams.



Implementation
--------------

The structure of the explorer is based on identifying unique values for a
certain hierarchy of keys. The basic mode of operation is this:

>    For a given value of this key find all unique values of that key

So for a hierarchy like this:

    location_str
        node_id
        node_type
    node_id
    version

The explorer will identify all of the unique `location_str` values, `node_id`
values, and `version` values present in the datastream for this particular
profile. Then, for each unique `location_str` the explorer will identify
each unique `node_id` and `node_type` present in that location.

