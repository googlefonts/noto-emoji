abc = ('A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z')

with open("emoji_u1f1e6.svg") as a_file:
    content: str = a_file.read()
    for i in range(1, 26):
        char_content = content.replace('A', abc[i])
        char_name = 'emoji_u1f1{}.svg'.format(hex(0xe6 + i)[2:])
        with open(char_name, 'w') as w_file:
            w_file.write(char_content)