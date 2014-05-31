End-to-End Example
==================

After you have GATD set up, you can use this example to verify that everything
is working correctly. Computer usage stats is a data source that reports basic
statistics of the machine it's running on (cpu usage, memory usage, etc).
Be sure to configure the computer stats source
(`computer_stats_udp_source.conf.example -> computer_stats_udp_source`) with the
correct information for your GATD install.

See `web/` directory for an example website that displays the output of the
computer usage statistics.
