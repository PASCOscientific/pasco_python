"""
dict[row] = column
{
    0: {0,1,2,3,4},
    1: {0,1,2,3,4},
    2: {0,1,2,3,4},
    3: {0,1,2,3,4},
    4: {0,1,2,3,4},
}
"""

alphabet = {
    ' ': {
        0: {},
        1: {},
        2: {},
        3: {},
        4: {}
    },
    'A': {
        0: {1,2,3,4},
        1: {0,2},
        2: {0,2},
        3: {1,2,3,4},
        4: {}
    },
    'B': {
        0: {0,1,2,3,4},
        1: {0,2,4},
        2: {0,2,4},
        3: {1,3},
        4: {}
    },
    'C': {
        0: {1,2,3},
        1: {0,4},
        2: {0,4},
        3: {0,4},
        4: {}
    },
    'D': {
        0: {0,1,2,3,4},
        1: {0,4},
        2: {0,4},
        3: {1,2,3},
        4: {}
    },
    'E': {
        0: {0,1,2,3,4},
        1: {0,2,4},
        2: {0,4},
        3: {},
        4: {}
    },
    'F': {
        0: {0,1,2,3,4},
        1: {0,2,4},
        2: {0},
        3: {},
        4: {}
    },
    'G': {
        0: {1,2,3},
        1: {0,4},
        2: {0,2,4},
        3: {0,2,3},
        4: {}
    },
    'H': {
        0: {0,1,2,3,4},
        1: {2},
        2: {2},
        3: {0,1,2,3,4},
        4: {}
    },
    'I': {
        0: {0,4},
        1: {0,1,2,3,4},
        2: {0,4},
        3: {},
        4: {}
    },
    'J': {
        0: {3},
        1: {0,4},
        2: {0,1,2,3},
        3: {0},
        4: {}
    },
    'K': {
        0: {0,1,2,3,4},
        1: {3},
        2: {1,3},
        3: {0,4},
        4: {}
    },
    'L': {
        0: {0,1,2,3,4},
        1: {4},
        2: {4},
        3: {},
        4: {}
    },
    'M': {
        0: {0,1,2,3,4},
        1: {1},
        2: {2},
        3: {1},
        4: {0,1,2,3,4}
    },
    'N': {
        0: {0,1,2,3,4},
        1: {1},
        2: {2},
        3: {3},
        4: {0,1,2,3,4}
    },
    'O': {
        0: {1,2,3},
        1: {0,4},
        2: {0,4},
        3: {1,2,3},
        4: {}
    },
    'P': {
        0: {0,1,2,3,4},
        1: {0,2},
        2: {0,2},
        3: {1},
        4: {}
    },
    'Q': {
        0: {1,2,3},
        1: {0,4},
        2: {0,4},
        3: {1,2,3,4},
        4: {4}
    },
    'R': {
        0: {0,1,2,3,4},
        1: {0,2},
        2: {0,2},
        3: {1,3,4},
        4: {}
    },
    'S': {
        0: {1,4},
        1: {0,2,4},
        2: {0,2,4},
        3: {0,3},
        4: {}
    },
    'T': {
        0: {0},
        1: {0},
        2: {0,1,2,3,4},
        3: {0},
        4: {0}
    },
    'U': {
        0: {0,1,2,3},
        1: {4},
        2: {4},
        3: {0,1,2,3},
        4: {}
    },
    'V': {
        0: {0,1,2},
        1: {3},
        2: {4},
        3: {3},
        4: {0,1,2}
    },
    'W': {
        0: {0,1,2,3,4},
        1: {3},
        2: {2},
        3: {3},
        4: {0,1,2,3,4}
    },
    'X': {
        0: {0,4},
        1: {1,3},
        2: {2},
        3: {1,3},
        4: {0,4}
    },
    'Y': {
        0: {0,1},
        1: {2,3,4},
        2: {0,1},
        3: {},
        4: {}
    },
    'Z': {
        0: {0,3,4},
        1: {0,2,4},
        2: {0,1,4},
        3: {0,4},
        4: {}
    },
    '0': {
        0: {0,1,2,3,4},
        1: {0,4},
        2: {0,1,2,3,4},
        3: {},
        4: {}
    },
    '1': {
        0: {1,4},
        1: {0,1,2,3,4},
        2: {4},
        3: {},
        4: {}
    },
    '2': {
        0: {1,4},
        1: {0,3,4},
        2: {0,2,4},
        3: {1,4},
        4: {}
    },
    '3': {
        0: {0,4},
        1: {0,2,4},
        2: {1,3},
        3: {},
        4: {}
    },
    '4': {
        0: {0,1,2},
        1: {2},
        2: {0,1,2,3,4},
        3: {},
        4: {}
    },
    '5': {
        0: {0,1,2,4},
        1: {0,2,4},
        2: {0,2,3,4},
        3: {},
        4: {}
    },
    '6': {
        0: {0,1,2,3,4},
        1: {0,2,4},
        2: {0,2,3,4},
        3: {},
        4: {}
    },
    '7': {
        0: {0},
        1: {0},
        2: {0,1,2,3,4},
        3: {},
        4: {}
    },
    '8': {
        0: {0,1,2,3,4},
        1: {0,2,4},
        2: {0,1,2,3,4},
        3: {},
        4: {}
    },
    '9': {
        0: {0,1,2,4},
        1: {0,2,4},
        2: {0,1,2,3,4},
        3: {},
        4: {}
    },
    '.': {
        0: {4},
        1: {},
        2: {},
        3: {},
        4: {}
    },
    ',': {
        0: {4},
        1: {3,4},
        2: {},
        3: {},
        4: {}
    },
    '-': {
        0: {2},
        1: {2},
        2: {},
        3: {},
        4: {}
    },
    '+': {
        0: {2},
        1: {1,2,3},
        2: {2},
        3: {},
        4: {}
    },
    '=': {
        0: {1,3},
        1: {1,3},
        2: {1,3},
        3: {},
        4: {}
    }
}

class Icons():
    def __init__(self):
        self.heart = {
            0: {1,2},
            1: {0,3},
            2: {1,4},
            3: {0,3},
            4: {1,2}
        }
        self.heart_sm = {
            0: {},
            1: {1,2},
            2: {2,3},
            3: {1,2},
            4: {}
        }
        self.smile = {
            0: {3},
            1: {0,4},
            2: {2,4},
            3: {0,4},
            4: {3}
        }
        self.sad = {
            0: {4},
            1: {0,3},
            2: {3},
            3: {0,3},
            4: {4}
        }
        self.surprise = {
            0: {3},
            1: {1,2,4},
            2: {2,4},
            3: {1,2,4},
            4: {3}
        }
        self.star = {
            0: {1,4},
            1: {1,3},
            2: {0,1,2},
            3: {1,3},
            4: {1,4}
        }
        self.arrow_top = {
            0: {2},
            1: {1},
            2: {0,1,2,3,4},
            3: {1},
            4: {2}
        }
        self.arrow_left = {
            0: {2},
            1: {1,2,3},
            2: {0,2,4},
            3: {2},
            4: {2}
        }
        self.arrow_bottom = {
            0: {2},
            1: {3},
            2: {0,1,2,3,4},
            3: {3},
            4: {2}
        }
        self.arrow_right = {
            0: {2},
            1: {2},
            2: {0,2,4},
            3: {1,2,3},
            4: {2}
        }
        self.arrow_topleft = {
            0: {0,1,2},
            1: {0,1},
            2: {0,2},
            3: {3},
            4: {4}
        }
        self.arrow_topright = {
            0: {4},
            1: {3},
            2: {0,2},
            3: {0,1},
            4: {0,1,2}
        }
        self.arrow_bottomleft = {
            0: {2,3,4},
            1: {3,4},
            2: {2,4},
            3: {1},
            4: {0}
        }
        self.arrow_bottomright = {
            0: {0},
            1: {1},
            2: {2,4},
            3: {3,4},
            4: {2,3,4}
        }
        self.alien = {
            0: {1,2,3,4},
            1: {0,1,3},
            2: {0,1,2,3,4},
            3: {0,1,3},
            4: {1,2,3,4}
        }


def get_icon(icon):
    matrix = []
    for col in icon:
        for row in icon[col]:
            matrix.append([col, row])
    return matrix


def get_word(word):
    display_screenshots = []

    if len(word) == 1:
        if word in alphabet:
            letter = alphabet[word]
        else:
            print(f'Letter {word} not found')
            return []

        matrix = []
        for col in letter:
            for row in letter[col]:
                matrix.append([col, row])
        display_screenshots.append(matrix)
        return [matrix]

    elif len(word) >1:
        word = f' {word}'
        word_dict = []
        for letter in word:
            if letter in alphabet:
                letter_dict = alphabet[letter]
            else:
                print(f'Letter {letter} not found')
                break

            for col in letter_dict:
                if len(letter_dict[col]) == 0 and letter != ' ':
                    break
                word_dict.append(letter_dict[col])
            word_dict.append({})

        for i in range(len(word_dict)):
            display_dict = word_dict[i:i+5]
            display_list = []
            for col in range(len(display_dict)):
                for row in display_dict[col]:
                    display_list.append([col, row])
            display_screenshots.append(display_list)

    return display_screenshots