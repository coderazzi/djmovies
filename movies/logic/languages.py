from movies.logic.gistfile1 import languages


def get_language(code):
    for c, lang in languages:
        if c==code:
            return lang
    print("Attention: unknown language:",code)
    return None



