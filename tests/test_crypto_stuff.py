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


def test_encrypt_text_list():
    pass

def test_decrypt_text_list():
    pass


def test_hash_text():
    pass


def test_create_hash_storage():
    pass
