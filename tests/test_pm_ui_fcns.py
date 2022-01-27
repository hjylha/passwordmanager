
import pytest

import fix_imports
import pm_ui_fcns


class TestOutput():

    def test_clear_screen(self, capsys):
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
        # pm_ui_fcns.clear_screen()
        # out, _ = capsys.readouterr()
        # assert not out


    def test_clear_clipboard(self):
        pm_ui_fcns.clear_clipboard()
        assert not pm_ui_fcns.pyperclip.paste()


    @pytest.mark.parametrize(
        'title, info', [
            ('some text', ('username', 'email', 'password', 'app', 'url')),
            ('bit of text', ('un', 'proper@e.mail', 'p4$$w0r|)', 'app', 'url'))
        ]
    )
    def test_print_info(self, capsys, title, info):
        pm_ui_fcns.print_info(title, info)

        email = info[1] if pm_ui_fcns.is_valid_email(info[1]) else '-'

        printed = f'{title}\nUsername: {info[0]}\nPassword: [HIDDEN]\nEmail: {email}\nApp name: {info[3]}\nApp url: {info[4]}\n'

        assert capsys.readouterr()[0] == printed


class TestInput():

    @pytest.mark.parametrize(
        'timeout', [3, 5, 8, 10, 15]
    )
    def test_end_prompt(self, monkeypatch, capsys, timeout):
        pm_ui_fcns.pyperclip.copy('important text in clipboard')
        monkeypatch.setattr(pm_ui_fcns.msvcrt, 'kbhit', lambda *args: True)
        monkeypatch.setattr(pm_ui_fcns.msvcrt, 'getch', lambda *args: b'\r')

        pm_ui_fcns.end_prompt(timeout)
        expected_text = f'\nPress ENTER to return back to menu. (This also clears clipboard)\n\rThis is done automatically in {timeout} seconds \n'

        assert capsys.readouterr()[0] == expected_text

        assert not pm_ui_fcns.pyperclip.paste()

    @pytest.mark.parametrize(
        'pw11, pw12, result', [
            tuple('g00d_passw0rd' for _ in range(3)),
            ('try1', 'try1notsame', 'try1'),
            ('try2', 'password', 'password')
        ]
    )
    def test_get_master_password(self, monkeypatch, pw11, pw12, result):
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
        
        monkeypatch.setattr(pm_ui_fcns.getpass, 'getpass', pw)

        assert pm_ui_fcns.get_master_password() == result


    @pytest.mark.parametrize(
        'pw', ['test_pw', 'gR8_8@s5w0r|)']
    )
    def test_ask_for_password(self, monkeypatch, pw):
        def write_pw(prompt=None):
            if prompt == 'Enter the master password: ':
                return pw
            return None
        
        monkeypatch.setattr(pm_ui_fcns.getpass, 'getpass', write_pw)

        assert pm_ui_fcns.ask_for_password() == pw


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
    def test_yes_or_no_question(self, monkeypatch, ans1, ans2, result):
        # with mock.patch('builtins.input', return_value='Y'):
        #     assert pm_ui_fcns.yes_or_no_question('blah') == 'y'
        count = [0]
        def answer(question=None):
            if 'Y/N' in question:
                count[0] += 1
                if count[0] == 1:
                    return ans1
                return ans2
            return None

        monkeypatch.setattr('builtins.input', answer)

        assert pm_ui_fcns.yes_or_no_question('big question?') == result
        

    @pytest.mark.parametrize(
        'app, url, username, email', [
            ('Some App', 'appurl.com', 'user_of_App', 'email?'),
            ('Youtube', 'youtube.com', 'fancy_username', 'e@mail.com')
        ]
    )
    def test_get_info_from_user(self, capsys, monkeypatch, app, url, username, email):
        def input_info(prompt=None):
            question = capsys.readouterr()[0]
            if 'name of the app' in question:
                return app
            if 'internet address' in question:
                return url
            if 'username' in question:
                return username
            if 'email' in question:
                return email
            return None

        monkeypatch.setattr('builtins.input', input_info)

        assert pm_ui_fcns.get_info_from_user() == (username, email, app, url)
        

    @pytest.mark.parametrize(
        'info', [
            ('Appname', None, None, None),
            (None, 'name_of_user', None, None),
            (None, None, 'invalid_email', None),
            (None, None, None, 'some_url'),
            ('Appname', 'new_user', 'invalid_email', None)
        ]
    )
    def test_get_changed_info(self, monkeypatch, info):
        keywords = ('app name', 'username', 'email', 'url')
        keys = ('app_name', 'username', 'email', 'url')
        new_info = {keys[i]: item for i, item in enumerate(info) if item is not None}
        
        def answer_to_yn(question=None):
            for word, key in zip(keywords, keys):
                if word in question and key in new_info.keys():
                    return 'y'
            return 'n'

        monkeypatch.setattr(pm_ui_fcns, 'yes_or_no_question', answer_to_yn)

        def write_new_info(prompt=None):
            for word, item in zip(keywords, info):
                if word in prompt:
                    return item
            return None

        monkeypatch.setattr('builtins.input', write_new_info)

        assert pm_ui_fcns.get_changed_info() == new_info


    @pytest.mark.parametrize(
        'num1, num2', [(i, 0) for i in range(7)]
    )
    def test_how_to_generate_pw(self, monkeypatch, num1, num2):
        count = [0]
        def selection(prompt=None):
            count[0] += 1
            if count[0] == 1:
                return str(num1)
            return str(num2)

        monkeypatch.setattr('builtins.input', selection)

        if num1 in [1, 2, 3]:
            assert pm_ui_fcns.how_to_generate_pw() == num1
        else:
            assert pm_ui_fcns.how_to_generate_pw() == 0


    @pytest.mark.parametrize(
        'num', ['nonsense', 0, 1, 2]
    )
    def test_generate_pw_generation(self, num):
        password = pm_ui_fcns.generate_pw(num)
        if num == 0:
            assert pm_ui_fcns.generate_pw(num) == ''
        if num in [1, 2]:
            assert len(password) == 20
            assert password != '20character_password'
            # should this check something more?
        else:
            # assert not password
            if num == 0:
                assert pm_ui_fcns.generate_pw(num) == ''
            elif not isinstance(num, int):
                assert password is None


    @pytest.mark.parametrize(
        'pw1, pw2, continue_no_typing, continue_not_same', [
            (('password',), ('password',), (None,), (None,)),
            (('',), ('',), ('n',), (None,)),
            (('pw',), ('notpw',), (None,), ('n',)),
            (('', 'pw'), ('', 'pw'), ('y',), (None,)),
            (('pw', 'npw'), ('notpw', 'npw'), (None,), ('y',)),
            (('pw', ''), ('notpw', ''), ('n',), ('y',)),
        ]
    )
    def test_generate_pw_user_pw(self, monkeypatch, pw1, pw2, continue_no_typing, continue_not_same):
        pw_count = [-1, -1]
        def write_pw(prompt=None):
            if 'you want' in prompt:
                pw_count[0] += 1
                return pw1[pw_count[0]]
            elif 'again' in prompt:
                pw_count[1] += 1
                return pw2[pw_count[1]]
            return None
        
        monkeypatch.setattr(pm_ui_fcns.getpass, 'getpass', write_pw)

        yn_count = [-1, -1]
        def answer_yn(question=None):
            if 'not type any' in question:
                yn_count[0] += 1
                return continue_no_typing[yn_count[0]]
            elif 'not the same' in question:
                yn_count[1] += 1
                return continue_not_same[yn_count[1]]
            return None
        
        monkeypatch.setattr(pm_ui_fcns, 'yes_or_no_question', answer_yn)

        if continue_not_same[-1] == 'n' or continue_no_typing[-1] == 'n':
            assert pm_ui_fcns.generate_pw(3) == ''
        else:
            assert pm_ui_fcns.generate_pw(3) == pw2[-1]


    @pytest.mark.parametrize(
        'num', [0, 1, 2]
    )
    def test_reveal_password(self, capsys, monkeypatch, num):
        password = '5tr0ng_p4$$wor|)'
        def choice(text=None):
            if 'password' in capsys.readouterr()[0]:
                return str(num)
            return None
        
        monkeypatch.setattr('builtins.input', choice)

        pm_ui_fcns.reveal_password(password)

        if num == 0:
            assert capsys.readouterr()[0] == ''
        elif num == 1:
            assert capsys.readouterr()[0] == 'Password has been copied to the clipboard.\n'
            assert pm_ui_fcns.pyperclip.paste() == password
        elif num == 2:
            assert capsys.readouterr()[0] == f'Password is: {password}\n'


    @pytest.mark.parametrize(
        'info', [
            (1, 'username', 'email', 'password', 'app', 'url'),
            ('not relevant', 'user', 'e@mail.com', '%&$_-,.:;^^^*', 'Goggle', 'address.com')
        ]
    )
    def test_obtain_password_no_reveal(self, capsys, info):
        pm_ui_fcns.obtain_password(info, False)
        
        printed = f'\nPassword found.\nApp: {info[4]}\nUsername: {info[1]}\nEmail: {info[2]}\nApp url: {info[5]}\n'
        assert capsys.readouterr()[0] == printed


    @pytest.mark.parametrize(
        'info, choice', [
            (('not relevant', 'user', 'e@mail.com', '%&$_-,.:;^^^*', 'Goggle', 'address.com'), 0),
            (('not relevant', 'user', 'e@mail.com', '%&$_-,.:;^^^*', 'Goggle', 'address.com'), 1),
            (('not relevant', 'user', 'e@mail.com', '%&$_-,.:;^^^*', 'Goggle', 'address.com'), 2)
        ]
    )
    def test_obtain_password_w_reveal(self, capsys, monkeypatch, info, choice):
        def choose(text=None):
            return str(choice)

        monkeypatch.setattr('builtins.input', choose)

        pm_ui_fcns.obtain_password(info, True)

        printed = f'\nPassword found.\nApp: {info[4]}\nUsername: {info[1]}\nEmail: {info[2]}\nApp url: {info[5]}\n'
        
        on_screen = capsys.readouterr()[0]
        assert printed in on_screen

        if choice == 1:
            assert 'Password has been copied to the clipboard.' in on_screen
            assert pm_ui_fcns.pyperclip.paste() == info[3]
        elif choice == 2:
            assert info[3] in on_screen
