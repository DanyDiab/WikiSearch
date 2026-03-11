import os
import bz2
import time
import hashlib
import requests

from tqdm import tqdm
from bs4 import BeautifulSoup, Tag

TIMEOUT = 60
CWD = os.getcwd()
CHUKN_SIZE = 8 * 1024 * 1024
DUMP_DIR = os.path.join(CWD, "wikidump")


def main():
    url = "https://dumps.wikimedia.org/other/mediawiki_content_current/enwiki/2026-03-01/xml/bzip2/"
    downloadFiles(url)



def downloadFiles(url: str):
    response = requests.get(url, stream=True, timeout=TIMEOUT)

    content = response.text

    soup = BeautifulSoup(content, "html.parser")
    atags = soup.find_all("a")

    os.makedirs(DUMP_DIR, exist_ok=True)
    otherTags = str(soup.find_all("pre")).split("\n")
    fileSizes = getFileBytesSize(otherTags[3:-1])

    shaMap = downloadSHASums(url,atags)

    downloadBZ2s(
        url=url,
        atags=atags,
        fileSizes=fileSizes,
        shaMap=shaMap
    )



def downloadBZ2s(url: str, atags: list[Tag], fileSizes: list[int], shaMap: dict[str:str]):
    for i,tag in enumerate(atags[2:]):
        href = tag.get("href")
        if href.endswith(".bz2"):
            link = url + href
            path = os.path.join(DUMP_DIR, href)
            sha = shaMap.get(href)
            downloadLink(link,path,fileSize=fileSizes[i],expectedSHA=sha)
            break



def downloadSHASums(url: str, atags: list[Tag]) -> dict[str:str]:
    SHA256s = atags[1].get("href")
    shaLink = url + SHA256s
    path = os.path.join(DUMP_DIR, "SHASUMS.txt")
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

        numbers.append(int("".join(num[::-1])))

    return numbers



def showProgress(curr, totalSize):
    progressBar = getattr(showProgress, "_progressBar", None)
    if progressBar is None or progressBar.total != totalSize:
        if progressBar is not None:
            progressBar.close()
        progressBar = tqdm(total=totalSize, unit="B", unit_scale=True, unit_divisor=1024)
        showProgress._progressBar = progressBar

    increment = max(curr - progressBar.n, 0)
    if increment:
        progressBar.update(increment)

    if curr >= totalSize:
        progressBar.close()
        showProgress._progressBar = None



def formatElapsedTime(seconds: float) -> str:
    minutes, remainingSeconds = divmod(seconds, 60)
    hours, remainingMinutes = divmod(int(minutes), 60)

    if hours:
        return f"{hours}h {remainingMinutes}m {remainingSeconds:.2f}s"
    if minutes >= 1:
        return f"{int(minutes)}m {remainingSeconds:.2f}s"
    return f"{seconds:.2f}s"



def downloadLink(link: str, filepath: str, fileSize: int = None, expectedSHA: str = None):
    bytesDownloaded = 0
    isBZ2 = True
    if(fileSize is None or expectedSHA is None):
        isBZ2 = False
    startTime = time.perf_counter()
    with requests.get(link, stream=True, timeout=TIMEOUT) as r:
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(CHUKN_SIZE):
                if not chunk:
                    continue

                bytesDownloaded += len(chunk)
                f.write(chunk)
                if isBZ2:
                    showProgress(bytesDownloaded, fileSize)

    elapsedTime = time.perf_counter() - startTime
    print(f"Download took {formatElapsedTime(elapsedTime)}")
    if isBZ2:
        print("Download Complete")
        shasMatch = validateSHA256(pathToCheck=filepath,expectedSHA=expectedSHA)
        print("do SHA's Match? " + str(shasMatch))
        if not shasMatch:
            return
        print("Now UnZipping File")
        unzipStartTime = time.perf_counter()
        unzipFile(filepath)
        unzipElapsedTime = time.perf_counter() - unzipStartTime
        print(f"Unzip took {formatElapsedTime(unzipElapsedTime)}")



def validateSHA256(pathToCheck: str, expectedSHA: str) -> bool:
    m = hashlib.sha256()
    with open(file=pathToCheck, mode="rb") as f:
        while chunk := f.read(CHUKN_SIZE):
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
