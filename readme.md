# Directories

## Third party library

All the third party libraries are stored in `third_party`.
In this project, following third party libraries are used:

+ Murmur hash library: [pymmh3](https://github.com/wc-duck/pymmh3)
+ ECDH library: [ecdsa](https://github.com/tlsfuzzer/python-ecdsa)
+ bitarray: [bitarray](https://pypi.org/project/bitarray/)

```bash
pip3 install bitarray 
```

## Experiments with library

To accomplish this project, we had done many experiments to learn different tools. All the experiment files are put into `demos` in order to check how to use these libraries.

## Root directory

The `utility.py` mainly contains the classes, functions we designed to accomplish this task.


# Introduction to different classes and functions

## Functions

### `murmurhash`

Generating a 3-bytes long hash. This operation discards the last byte of murmur hash 32

### `bytearr_hex_to_str` and `str_hex_to_bytearr`

These two functions performs the conversion between `bytearray` and `str`. Mainly used for debugging


## classes

### `EncMgr`

The `EncMgr` manages `ephid` and generates `encid`. 

+ The class member `pub_key` is actually the current `ephid`. 
+ The class member function `get_shared()` returns the `encid` generated for bloom filter.
+ The class member function `new_priv_key()` helps you to generate new `ephid`.

### `bloom_filter`

A simple bloom filter implemented with `bitarray`. 

+ `put()` function insert a new record into bloom filter 
+ `get()` function check whether an item was recorded in this bloom filter

### `client`  

The `client` mainly focus on broadcasting and listening. It also decides when a new `ephid` should be generated and when to upload `QBF` and `CBF` and etc.
