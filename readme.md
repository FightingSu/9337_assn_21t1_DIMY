# Directories

## Third party library

All the third party libraries are stored in `third_party`.
In this project, following third party libraries are used:

+ Murmur hash library: [pymmh3](https://github.com/wc-duck/pymmh3)
+ ECDH library: [ecdsa](https://github.com/tlsfuzzer/python-ecdsa)
+ bitarray: [bitarray](https://pypi.org/project/bitarray/)
+ Shamir's secret sharing: [shamir-mnemonic](https://github.com/trezor/python-shamir-mnemonic)
+ Requests: [Requests](https://docs.python-requests.org/en/master/)

```bash
pip3 install bitarray shamir-mnemonic requests
```

Please note that you may **failed to install bitarray using `pip`**, because it will compile some C/C++ code in your computer. It requires environment building C/C++ project which you may not have. If that happens, you may go to [this website](https://www.lfd.uci.edu/~gohlke/pythonlibs/#bitarray) (seems for windows only) to download pre-compiled binaries to install.

*Note: For shamir's secret sharing, if is (3,6) mode: creates 6 shares and 3 shares are enough to encrypt the message so only 3 shares should be provided while decrypting or it will raise an error.*

## Experiments

To accomplish this project, we had done many experiments to learn different tools. All the experiment files are put into `demos` in order to check how to use these libraries. 

In addition, we wrote many functions/classes too, and the experiments with them are located in `demos` too.

## Root directory

The `utility.py` mainly contains the classes, functions we designed to accomplish this task.


# Introduction to different classes and functions

## Functions

### `bytearr_hex_to_str` and `str_hex_to_bytearr`

These two functions performs the conversion between `bytearray` and `str`. Mainly used for debugging


### `query_contact` and `upload_contact`

These two functions mainly contributes to communication with backend server.

+ `query_contact` sends QBFs to the server and get result.
+ `upload_contact` sends CBFs to the server and get result.


### `generate_identifier`

Generating a 3-bytes long hash. This operation discards the last byte of murmur hash 32

## classes

### `enc_mgr`

The `enc_mgr` manages `ephid` and generates `encid`. 

+ The class member `pub_key` is actually the current `ephid`. 
+ The class member function `get_shared()` returns the `encid` generated for bloom filter.
+ The class member function `new_priv_key()` helps you to generate new `ephid`.

### `bloom_filter`

A simple bloom filter implemented with `bitarray`. 

+ `put()` function insert a new record into bloom filter
+ `get()` function check whether an item was recorded in this bloom filter
+ `combine_filters()` a static member function which combine filters together

### `client`  

The `client` mainly focus on broadcasting and listening. It also decides when a new `ephid` should be generated and when to upload `QBF` and `CBF` and etc.


### entered by heyue
### part1:

ephid_frag is a dictionary, which stored all the received hash id and shared messages.
like this:
{
Hash_id_1:shared_msg_1, shared_message_2;
Hash_id_2:shared_msg-1
 }
 Note that every hash id won't have more then two shared messages
 As onece three messages are get, an EphID will be generated and the hash id
 will be deleted from this dictionary.

 It's very possiblt for the dictionary to be very long.
 For example, Bob and Alice are in a park.
 Bob is sitting on a banch and Alice is walking around.
 Alice get close to Bob and then walk away, this costs 20 seconds
 and Bob will recieve messages from Alice like this:
 {
 Hash_id_Alice_1 : shared_msa_1,shared_msa_2   
 }
 Let us suppose 1 minute later Alice return and this time,
 she already changed her Ephid so her hash id is different now.
 The dictionary would look like this:
 {
 Hash_id_Alice_1 : shared_msa_1,shared_msa_2  
 Hash_id_Alice_2 : shared_msa_1,shared_msa_2
 }
 So Hash_id_Alice_1 will remain in the dictionary forever if we don't clean it
 So we reset the Dictionary every 10 minutes.
 When a new DBF is created(10 minutes), the dictionary will reset to empty.
 And because of the situation mentioned above, the total shares recieved won't always be
 1,2,3,1,2,3... 
 It may be 1,2,3,4,2,3,4....


### part2
To keep the device to have only 6 DBFs,
we create a list to contain all the 6 DBFs,
once a new DBF is created, it would be append into the list.
And we use pop to kick out the oldest DBF, while pop won't release
the room the DBF takes, we use del to release the room occupied by the DBF
As a DBF is a really long array, we believe this is important.

### part3
we are know using pip3 install pycryptodomex
pycryptodomex contains a shamir class.
to install it on Pi, as we are using python3, please enter pip3 install pycryptodomex