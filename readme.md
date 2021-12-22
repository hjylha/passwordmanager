
<!-- inspired by github.com/KalleHallden/pwManager -->

A console application to manage a local database of passwords.

![password manager in use](pm_screenshot2.png)

The application actually uses three databases:
* one containing the master key, which can be decrypted with master password and salt
* one containing the keys, which can be decrypted with the master key
* one containing the password data, which can be decrypted with keys


To start the password manager, just use command
`python pm.py`



### Libraries/modules used:
* cryptography
* argon2-cffi is used to hash the master password and verify it
* pyperclip is used for copying passwords to the clipboard
* pytest
<!-- * base64
* getpass
* sqlite3
* os -->

The cryptography library is used to encrypt and decrypt data. Master password is hashed using argon2-cffi, which then is also used for verifying the password. User has the option of copying the passwords to the clipboard. This makes use of the pyperclip module. Databases are handled using sqlite3 module. Testing is done using pytest.

More detailed requirements can be found in requirements.txt.


<!-- ### Currenly working on -->

<!-- Changing to a more complicated database structure with three encrypted databases:
* one containing the master key, which can be decrypted with master password and salt
* one containing the keys, which can be decrypted with the master key
* one containing the password data,which can be decrypted with keys -->


<!-- ### Possible improvements
* Encryption/decryption/hashing can most likely be improved
* Replacing 'input' with something else
* Everyone wants a fancy GUI... -->
