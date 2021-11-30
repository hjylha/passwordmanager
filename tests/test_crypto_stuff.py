from pathlib import Path
import pytest

import fix_imports
import crypto_stuff as cs


@pytest.fixture
def pw():
    return "1234"

@pytest.fixture
def salt():
    salt_path = Path(__file__).parent.parent / "salt.txt"
    with open(salt_path, "rb") as s:
        salt = s.read()
    return salt

@pytest.fixture
def iteration_num():
    return 157

# this is tested immediately below
@pytest.fixture
def fernet_thing(pw, salt):
    return cs.do_crypto_stuff(pw, salt, 37)


def test_do_crypto_stuff(pw, salt):
    for num_of_iter in range(1, 1000, 17):
        assert isinstance(cs.do_crypto_stuff(pw, salt, num_of_iter), cs.Fernet)


def test_encrypt_text(fernet_thing):
    text = "very secret"
    encryptions = [text]
    for _ in range(7):
        encryption = cs.encrypt_text(text, fernet_thing)
        assert encryption not in encryptions
        encryptions.append(encryption)
        

def test_decrypt_text(fernet_thing):
    text = "very secret"
    encrypted = cs.encrypt_text(text, fernet_thing)
    assert text == cs.decrypt_text(encrypted, fernet_thing)


def test_encrypt_text_list(fernet_thing):
    text_list = ["first", "second", "third"]
    encryptions = [text_list]
    for _ in range(5):
        encryption = cs.encrypt_text_list(text_list, fernet_thing)
        assert len(encryption) == len(text_list)
        for i, e_text in enumerate(encryption):
            assert e_text not in [item[i] for item in encryptions]

def test_decrypt_text_list(fernet_thing):
    text_list = ["first", "second", "third"]
    e_text_list = cs.encrypt_text_list(text_list, fernet_thing)
    assert text_list == cs.decrypt_text_list(e_text_list, fernet_thing)


def test_hash_text(salt, iteration_num):
    text = "all good"
    hashed_text = cs.hash_text(text, salt, iteration_num)
    assert isinstance(hashed_text, bytes)
    assert len(hashed_text) == 32


def test_create_hash_storage(salt, iteration_num):
    text = "all good"
    hash_storage = cs.create_hash_storage(text, salt, iteration_num)
    assert len(hash_storage) == 48
    assert hash_storage == salt + cs.hash_text(text, salt, iteration_num)


def test_hash_password():
    pwd = "s3cur3 p455w0rd"
    assert isinstance(cs.hash_password(pwd), str)

def test_check_password_hash():
    pwd = "s3cur3 p455w0rd"
    hash = cs.hash_password(pwd)
    assert cs.check_password_hash(hash, pwd)
    assert not cs.check_password_hash(hash, "not right")


def test_hash_tuple():
    something = ("first", "second", "third")
    hashed_tuple = cs.hash_tuple(something)
    assert len(hashed_tuple) == len(something)
    for item in hashed_tuple:
        assert isinstance(item, str)

def test_check_tuple():
    something = ("first", "second", "third")
    hashed_tuple = cs.hash_tuple(something)
    assert cs.check_tuple(hashed_tuple, something)

    something_else = ("a", "second", "third")
    assert not cs.check_tuple(hashed_tuple, something_else)


def test_get_characters():
    all_chars = cs.get_characters()
    some_chars = cs.get_characters(1)
    letters = "abcdefghijklmnopqrstuvwxyz"
    numbers = "0123456789"
    extra_chars = '(,._-*~"<>/|!@#$%^&)+='
    assert letters in all_chars
    assert letters in some_chars
    assert letters.upper() in all_chars
    assert letters.upper() in some_chars
    assert numbers in all_chars
    assert numbers in some_chars
    assert extra_chars in all_chars
    for char in extra_chars:
        assert char not in some_chars


def test_generate_password():
    pwd = cs.generate_password()
    assert len(pwd) == 20
