import requests
import os
from bs4 import BeautifulSoup
import bz2



def main():
    url = "https://dumps.wikimedia.org/other/mediawiki_content_current/enwiki/2026-03-01/xml/bzip2/"
    response = requests.get(url, stream=True)

    content = response.text

    soup = BeautifulSoup(content, "html.parser")
    atags = soup.find_all("a")
    otherTags = str(soup.find_all("pre")).split("\n")
    SHA256s = atags[1].get("href")
    shaLink = url + SHA256s

    fileSizes = getFileBytes(otherTags[3:-1])
    
    os.makedirs("wikidump", exist_ok=True)
    path = os.path.join("wikidump", "SHASUMS.txt")
    
    downloadLink(shaLink,path, 1)
    for i,tag in enumerate(atags[2:]):
        href = tag.get("href")
        if href.endswith(".bz2"):
            link = url + href
            path = os.path.join("wikidump", href)
            downloadLink(link,path,fileSize=fileSizes[i])
            break



def getFileBytes(lines: list[str]) -> list[int]:
    numbers = []
    for line in lines:
        num = []
        for c in line[::-1].strip():
            if not c.isdigit():
                break
            
            num.append(c)
        number = int("".join(num[::-1]))
        numbers.append(number)

    return numbers
    

def showProgress(curr, totalSize):
    progress = (curr / totalSize) * 100
    print(f"{progress:.2f}%",end="\r",flush=True)



def downloadLink(link: str, filepath: str, fileSize: int):
    bytesDownloaded = 0
    chunkSize = 8192
    with requests.get(link, stream=True) as r:
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunkSize):
                bytesDownloaded += chunkSize
                f.write(chunk)
                showProgress(bytesDownloaded,fileSize)


def unzipFile(filepath: str):
    with bz2.open(filepath, 'rb') as f_in:
        with open('decompressed.txt', 'wb') as f_out:
            f_out.write(f_in.read())
        
if __name__ == "__main__":
    main()