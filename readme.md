
<!-- inspired by github.com/KalleHallden/pwManager -->

A console application to manage a local database of passwords.

![password manager in use](pm_screenshot2.png)

The way to encrypt/decrypt the data was taken from an example in the documentation of the cryptography library.

To start the password manager, just use command
`python pm.py`



### Libraries/modules used:
* cryptography
* argo2-cffi
* pyperclip
* pytest (fot testing)
<!-- * base64
* getpass
* sqlite3
* os -->

More detailed requirements can be found in requirements.txt.


### Currenly working on

Changing to a more complicated database structure with three encrypted databases:
* one containing the master key, which can be decrypted with master password and salt
* one containing the keys, which can be decrypted with the master key
* one containing the password data,which can be decrypted with keys


### Possible improvements
* Encryption/decryption/hashing can most likely be improved
* Replacing 'input' with something else
* Everyone wants a fancy GUI...
