GATD Configuration
==================

All parameters for GATD that either configure how GATD operates or are
constants shared between multiple modules are set in the `gatd.config` file.
An example version is stored in `gatd.config.example`. These settings should
be updated for your specific configuration.


Usage
-----

The Python module `gatdConfig.py` creates objects and attributes for all of the
parameters specified in `gatd.config`. This makes it very easy to use the
configuration in other Python modules.

In another module simply import the config module:

    import gatdConfig

Then access the paramters like so:

    gatdConfig.mongo.HOST

Note that all of the attribute names are capitalized so that they stand out
as constants in the code.
