import requests
import os
from bs4 import BeautifulSoup, Tag
import bz2
import hashlib


def main():
    url = "https://dumps.wikimedia.org/other/mediawiki_content_current/enwiki/2026-03-01/xml/bzip2/"
    downloadFiles(url)



def downloadFiles(url: str):
    response = requests.get(url, stream=True)

    content = response.text

    soup = BeautifulSoup(content, "html.parser")
    atags = soup.find_all("a")
    
    dumpDir = "../wikidump"
    os.makedirs(dumpDir, exist_ok=True)
    otherTags = str(soup.find_all("pre")).split("\n")
    fileSizes = getFileBytesSize(otherTags[3:-1])
    
    shaMap = downloadSHASums(url,atags,dumpDir)
    
    downloadBZ2s(url=url,atags=atags,dir=dumpDir,fileSizes=fileSizes,shaMap=shaMap)


def downloadBZ2s(url: str, atags: list[Tag], dir: str, fileSizes: list[int], shaMap: dict[str:str]):
    for i,tag in enumerate(atags[2:]):
        href = tag.get("href")
        if href.endswith(".bz2"):
            link = url + href
            path = os.path.join(dir, href)
            sha = shaMap.get(href)
            downloadLink(link,path,fileSize=fileSizes[i],expectedSHA=sha)
            break


def downloadSHASums(url: str, atags: list[Tag], dir: str) -> dict[str:str]:
    SHA256s = atags[1].get("href")
    shaLink = url + SHA256s
    path = os.path.join(dir, "SHASUMS.txt")
    downloadLink(shaLink,path)

    shaMap = parseShaTxt(path)
    return shaMap

def parseShaTxt(filePath: str) -> dict[str:str]:
    with open(filePath,mode="r", newline="") as f:
        content = f.read()
        split = content.split("\n")
    shaMap = {}
    for row in split:
        if not row: continue
        rowSplit = row.split(" ")
        # grab sum
        sha = rowSplit[0]
        # grab filePath
        filePath = rowSplit[2]
        shaMap[filePath] = sha
    return shaMap

def getFileBytesSize(lines: list[str]) -> list[int]:
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



def downloadLink(link: str, filepath: str, fileSize: int = None, expectedSHA: str = None):
    bytesDownloaded = 0
    chunkSize = 8192
    isBZ2 = True
    if(fileSize is None or expectedSHA is None):
        isBZ2 = False
    with requests.get(link, stream=True) as r:
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunkSize):
                bytesDownloaded += chunkSize
                f.write(chunk)
                if isBZ2: 
                    showProgress(bytesDownloaded,fileSize)
    if isBZ2: 
        print("Download Complete")
        shasMatch = validateSHA256(pathToCheck=filepath,expectedSHA=expectedSHA)
        print("do SHA's Match? " + shasMatch)
        if not shasMatch:
            return
        print("Now UnZipping File")
        unzipFile(filepath)

def validateSHA256(pathToCheck: str, expectedSHA: str) -> bool:
    chunkSize = 8192

    m = hashlib.sha256()
    with open(file=pathToCheck, mode="rb") as f:
        while chunk := f.read(chunkSize):
            m.update(chunk)
    sha = m.hexdigest()
    return sha == expectedSHA

def unzipFile(filepathToDecompress: str):
    fileName = filepathToDecompress.replace(".bz2","")
    with bz2.open(filepathToDecompress, 'rb') as f_in:
        with open(fileName, 'wb') as f_out:
            f_out.write(f_in.read())
        
if __name__ == "__main__":
    main()