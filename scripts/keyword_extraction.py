from yake import KeywordExtractor

y = KeywordExtractor(windowsSize = 2)

print(y.extract_keywords("prove that the mapping f:A->B is a bijection if and only if |A| = |B|"))
