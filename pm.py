
import sys
from pm_ui import PM_UI
from pm_ui_fcns import clear_screen, end_prompt, yes_or_no_question, ask_for_password

# mode: 0=normal, 1=add, 2=get, 3=list all apps
def password_manager(mode: int =0):
    # starting text
    # print('Welcome to my Password Manager\n')
    existing_and_not_default = True if mode else False
    # if mode:
    #     existing_and_not_default = True 
    pm_ui = PM_UI(existing_and_not_default)

    if pm_ui.pm is None:
        return
    
    # un = 'placeholder username'
    if pm_ui.pm.master_key is None:
        # un, master_pw = ask_for_username_and_password()
        master_pw = ask_for_password()
        if pm_ui.pm.check_master_password(master_pw):
            pm_ui.pm.set_name_lists()
        else:
            print('Incorrect username and password')
            return

    # no need for master pw anymore
    master_pw = None
    clear_screen()
    # print(f'Password Manager for user {un}\n')
    if mode == 1:
        pm_ui.add_password()
        return
    if mode == 2:
        pm_ui.find_password_for_app()
        return
    if mode == 3:
        pm_ui.list_apps()
        return
    
    # the program loop
    while True:
        print('What do you want to do?')
        print('(1) Add a new password')
        print('(2) Change a password')
        print('(3) Retrieve a password')
        print('(4) Change information related to a password')
        print('(5) Show a list of apps with passwords')
        print('(7) Delete a password')
        print('(9) Clear Screen')
        print('(0) Exit')
        action = input()
        if action == '0':
            ans = yes_or_no_question('Are you sure you want to exit Password Manager?')
            if ans.lower() == 'y':
                clear_screen()
                return
        elif action == '1':
            pm_ui.add_password()
            end_prompt()
        elif action == '2':
            pm_ui.change_password()
            end_prompt()
        elif action == '3':
            pm_ui.find_password_for_app()
            end_prompt()
        elif action == '4':
            pm_ui.change_password_info()
            end_prompt()
        elif action == '5':
            pm_ui.list_apps()
            end_prompt()
        elif action == '7':
            pm_ui.delete_password()
            end_prompt()
        elif action == '9':
            clear_screen()
        else:
            print('Invalid input. Please choose one of the options.\n')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if 'add' in sys.argv[1]:
            password_manager(1)
        elif 'get' in sys.argv[1]:
            password_manager(2)
        elif 'list' in sys.argv[1] or 'app' in sys.argv[1]:
            password_manager(3)
        else:
            print(f'Not a valid parameter: {sys.argv[1]}')
    else:
        password_manager()

