
import unittest.mock as mock
import pytest

import fix_imports

import pm_ui
from pm_ui import PM_UI



def test_clear_screen(capsys):
    pass
    # THIS DOES NOT WORK
    # start_text = 'some test is being written here...'
    # print(start_text)
    # out, _ = capsys.readouterr()
    # assert out == f'{start_text}\n'
    # second_text = 'more text...'
    # print(second_text)
    # # out, _ = capsys.readouterr()
    # # assert out == f'{start_text}\n{second_text}\n'
    # pm_ui.clear_screen()
    # out, _ = capsys.readouterr()
    # assert not out


def test_clear_clipboard():
    pm_ui.clear_clipboard()
    assert pm_ui.pyperclip.paste() == 'nothing here'


@pytest.mark.parametrize(
    'pw11, pw12, result', [
        tuple('g00d_passw0rd' for _ in range(3)),
        ('try1', 'try1notsame', 'try1'),
        ('try2', 'password', 'password')
    ]
)
def test_get_master_password(monkeypatch, pw11, pw12, result):
    count = [0]
    def pw(prompt):
        if prompt == 'Please enter master password for password manager: ':
            if count[0] == 0:
                return pw11
            return result
            # if prompt in capsys.readouterr()[0]:
            #     return result
            # return pw11
        elif prompt == 'Please enter the master password again: ':
            count[0] += 1
            if count[0] == 1:
                return pw12
            return result
            # if prompt in capsys.readouterr()[0]:
            #     return result
            # return pw12
            
        else:
            return None
    
    monkeypatch.setattr(pm_ui.getpass, 'getpass', pw)

    assert pm_ui.get_master_password() == result


@pytest.mark.parametrize(
    'pw', ['test_pw', 'gR8_8@s5w0r|)']
)
def test_ask_for_password(monkeypatch, pw):
    def write_pw(prompt=None):
        if prompt == 'Enter the master password: ':
            return pw
        return None
    
    monkeypatch.setattr(pm_ui.getpass, 'getpass', write_pw)

    assert pm_ui.ask_for_password() == pw


@pytest.mark.parametrize(
    'ans1, ans2, result', [
        ('Y', None, 'y'),
        ('y', None, 'y'),
        ('N', None, 'n'),
        ('n', None, 'n'),
        ('nonsense', 'y', 'y'),
        ('nonsense', 'Y', 'y'),
        ('nonsense', 'N', 'n'),
        ('nonsense', 'n', 'n')
    ]
)
def test_yes_or_no_question(monkeypatch, ans1, ans2, result):
    # with mock.patch('builtins.input', return_value='Y'):
    #     assert pm_ui.yes_or_no_question('blah') == 'y'
    count = [0]
    def answer(question=None):
        if 'Y/N' in question:
            count[0] += 1
            if count[0] == 1:
                return ans1
            return ans2
        return None

    monkeypatch.setattr('builtins.input', answer)

    assert pm_ui.yes_or_no_question('big question?') == result
    


def test_get_info_from_user():
    pass


def test_get_changed_info():
    pass


def test_print_info():
    pass


def test_how_to_generate_pw():
    pass


def test_generate_pw():
    pass