import urllib.request
try:
    ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
    print("YOUR_PYTHON_PUBLIC_IP:", ip)
except Exception as e:
    print("Error:", e)
