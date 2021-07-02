import random

def characters_by_type():
    lower_letters = "abcdefghijklmnopqrstuvwxyz"
    upper_letters = lower_letters.upper()
    numbers = "0123456789"
    extra_characters = '(,._-*~"<>/|!@#$%^&)+='
    return (lower_letters, upper_letters, numbers, extra_characters)

# with or without extra characters (choice=0 or 1)
def generate_password(num_of_chars=16, choice=0):
    available_character_types = characters_by_type()
    if choice == 0:
        possible_chars = random.choices(available_character_types, k=num_of_chars)
        pw = []
        for chars in possible_chars:
            pw.append(random.choice(chars))
        return ''.join(pw)
    elif choice == 1:
        indices = random.choices([0, 1, 2], k=num_of_chars)
        pw = []
        for index in indices:
            char = random.choice(available_character_types[index])
            pw.append(char)
        return ''.join(pw)
    else:
        print("Error: The value of 'choice' is not 0 or 1")
