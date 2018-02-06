from gistfile1 import languages


def get_language(code):
    for c, lang in languages:
        if c==code:
            return lang
    return None



