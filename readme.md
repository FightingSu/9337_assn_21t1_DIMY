# Directories

All the third party library are stored in `third_party`.

To accomplish this project, we had done many experiments to learn different tools. All the experiment files are put into `demos` in order to check how to use the libraries.

The `utility.py` mainly contains the classes, functions we designed to accomplish this task.

# Introduction to different classes

## `EncMgr`

The `EncMgr` manages `ephid` and generates `encid`. 

+ The class member `pub_key` is actually the `ephid` using for now. 
+ The class member function `get_shared()` returns the `encid` generated for bloom filter. 
+ The class member function `new_priv_key()` helps you to generate new `ephid`.

## `client`

The `client` mainly focus on broadcasting and listening. It also decides when a new `ephid` should be generated and when to upload `QBF` and `CBF` and etc.
