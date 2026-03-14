import os
import bz2
import time
import requests

from tqdm import tqdm
from bs4 import BeautifulSoup, Tag

TIMEOUT = 60
CHUKN_SIZE = 8 * 1024 * 1024

URL = "https://dumps.wikimedia.org/other/mediawiki_content_current/enwiki/2026-03-01/xml/bzip2/"

CWD = os.getcwd()
DUMP_DIR = os.path.join(CWD, "wikidump")
os.makedirs(DUMP_DIR, exist_ok=True)



def get_page_content() -> BeautifulSoup:
    return BeautifulSoup(
        requests.get(URL, stream=True, timeout=TIMEOUT).text,
        features="html.parser"
    )



def get_page_aspect(soup: BeautifulSoup, tag: str):
    return soup.find_all(tag)



def downloadBZ2(bz2_file: Tag, fileSize: int, filepath: str):
    href = bz2_file.get("href")
    if href.endswith(".bz2"):
        link = URL + href
        downloadLink(
            link,
            filepath,
            fileSize=fileSize
        )
        return



def downloadSHASums(sha_file: Tag) -> dict[str, str]:
    shaLink = URL + sha_file
    path = os.path.join(DUMP_DIR, "SHASUMS.txt")
    downloadLink(shaLink, path)

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



def downloadLink(link: str, filepath: str, fileSize: int = None):
    bytesDownloaded = 0
    startTime = time.perf_counter()
    with requests.get(link, stream=True, timeout=TIMEOUT) as r:
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(CHUKN_SIZE):
                if not chunk:
                    continue

                bytesDownloaded += len(chunk)
                f.write(chunk)
                if fileSize is not None:
                    showProgress(bytesDownloaded, fileSize)

    elapsedTime = time.perf_counter() - startTime
    print(f"Download took {formatElapsedTime(elapsedTime)}")
        



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

