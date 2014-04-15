GATD Scripts
============

These scripts help administer a GATD instance.

- `explorer_edit.py`: Use this to setup the interesting keys the explorer
service should be looking for.
- `formatter_test.py` Use this to test a new formatter before adding it to
GATD. `formatter_test.py` will run a test stream against the new/edited
formatter and show you the results.
- `gateway_edit.py`: This lets you edit information corresponding to the upper
64 bits of the IPv6 address of the node that sent a packet. This is useful
for something like tagging all nodes with the same prefix with a location.
- `meta_edit.py`: This adjusts the meta information the system appends to
incoming packets.
- `profile.py`: Use this to create a new Profile ID or view and existing one.