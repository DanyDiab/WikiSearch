import requests
import os
from bs4 import BeautifulSoup



def main():
    url = "https://dumps.wikimedia.org/other/mediawiki_content_current/enwiki/2026-03-01/xml/bzip2/"
    response = requests.get(url, stream=True)

    content = response.text

    soup = BeautifulSoup(content, "html.parser")
    atags = soup.find_all("a")
    otherTags = str(soup.find_all("pre")).split("\n")
    print(otherTags[3])
    SHA256s = atags[1].get("href")
    shaLink = url + SHA256s
    
    os.makedirs("wikidump", exist_ok=True)
    path = os.path.join("wikidump", "SHASUMS.txt")
    downloadLink(shaLink,path)
    return
    for tag in atags[2:]:
        href = tag.get("href")
        if href.endswith(".bz2"):
            link = url + href
            path = os.path.join("wikidump", href + ".bz2")
            downloadLink(link,path)
            break


def downloadLink(link: str, filepath: str):
    with requests.get(link, stream=True) as r:
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)




if __name__ == "__main__":
    main()