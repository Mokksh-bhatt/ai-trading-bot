import codecs

path = 'backend/requirements.txt'
try:
    with codecs.open(path, 'r', 'utf-16') as f:
        content = f.read()
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(content)
    print("Converted to UTF-8")
except Exception as e:
    print("Error:", e)
