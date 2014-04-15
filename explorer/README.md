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


Usage
-----

The explorer module runs as a service with GATD. It provides a simple HTTP based
JSON API to retrieve information about the current streams. The following are
valid URLs:

- `/explore/all`: Returns a JSON blob representing the streams in GATD.
```
{
	"explore": {profile_id: {
                               key: {
                                       value: {
                                                 key: {
                                                        value: {}
                                                      }
                                              },
                                       value: {}
                                    }
                            }
               },
	"meta": {profile_id: {
	                       "meta1": value,
	                       "meta2": value
	                     }
	        }
}
```
- `/explore/profile/<profile_id>`: Returns the same key value hierarchy
as `/explore/all` except for only one Profile ID and without the meta
information.
- `/explore/profile/meta/<profile_id>`: Returns the meta information
for a particular Profile ID.
