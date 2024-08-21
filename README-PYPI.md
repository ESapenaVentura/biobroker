# Biobroker

This repository contains the source code for the `Biobroker` python package. This package contains
multiple utilities, but the overall philosophy/goal can be described in a phrase:


>Given an input file of any type containing metadata about entities, broker it to any archive
> and return a human-readable result.

I understand that this is a very ambitious project; for starters, the variety of existing archives
is way too high. For now, this package is being developed by extending my knowledge on the european
genomics/bio archives hosted by EMBL-EBI. It may be that some archives can't just be adapted, but I
will be very happy if this library can be extended to just work with enough archives to ensure a biology
laboratory can set up an automatic brokering process that works for them.

## Install

```shell
pip3 install biobroker
```

## Usage

This library does not support CLI access at the moment (Maybe in the future I could think of a CLI; although I would
much rather have a simple GUI). As such, you will have to install and write scripts using the objects provided.

For usage, please see the examples/ folder in the [repository](https://github.com/ESapenaVentura/biobroker).

For extensive documentation about the overall infrastructure and each class, please see the
[ReadTheDocs page](https://biobroker.readthedocs.io/en/latest/)
