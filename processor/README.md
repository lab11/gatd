GATD - Processors
=================

Processors take formatted data and apply some transformation to it. In contrast
to formatters, processors can be stateful and complex if needed.
Each processor binds to the queue coming out of the formatter, takes any packets
it needs to process, generates any new packets, and sends the new packets
back to the formatter. The formatter then puts the new packets in the database
and puts the processed packets back in the queue. In this way, packets could
be processed many times.