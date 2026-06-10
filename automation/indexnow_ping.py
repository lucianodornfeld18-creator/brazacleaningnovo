# -*- coding: utf-8 -*-
"""Ping IndexNow (Bing + outros) para uma ou mais URLs. Key file ja deployado na raiz do site.
Uso: python automation/indexnow_ping.py <url> [<url> ...]
Nao-fatal por design: falha imprime aviso e sai 0.
"""
import sys, urllib.request, urllib.parse

KEY = "8977f066a9364d3c9849989f50349049"
KEY_LOCATION = f"https://brazacleaning.com/{KEY}.txt"

def ping(url):
    q = urllib.parse.urlencode({"url": url, "key": KEY, "keyLocation": KEY_LOCATION})
    req = urllib.request.Request(f"https://api.indexnow.org/indexnow?{q}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status

def main():
    urls = sys.argv[1:]
    if not urls:
        print("uso: indexnow_ping.py <url> [...]")
        return
    for u in urls:
        try:
            print(f"indexnow {u} -> HTTP {ping(u)}")
        except Exception as e:
            print(f"indexnow {u} FALHOU (nao-fatal): {e}")

if __name__ == "__main__":
    main()
