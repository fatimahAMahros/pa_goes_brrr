from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# 1. Create the factory
factory = StemmerFactory()

# 2. Get the default dictionary
dictionary = factory.get_words_cache()

# 3. Add your protected words/locations to the dictionary
# This tells Sastrawi: "These are already root words, don't touch them!"
protected_locations = ['sememi', 'benowo', 'rungkut', 'kedung', 'mei']
for word in protected_locations:
    dictionary.add(word)

# 4. Create the stemmer using the updated dictionary
stemmer = factory.create_stemmer()

# Testing it out
text = "pdam daerah sememi mati min"
print(stemmer.stem(text)) 
# Output: "pdam daerah sememi mati min" (instead of 'mem')