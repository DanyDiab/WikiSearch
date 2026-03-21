import tf_idf as tf_idf

def makeLinkMap(links: list) -> map:
    linkMap = {}
    for doc_id, link_id in links:
        if doc_id not in linkMap:
            linkMap[doc_id] = set()
        linkMap[doc_id].add(link_id)
    return linkMap
def iterate(base_set: list, k: int):
    z = [1] * len(base_set)
    xAuth = z
    yHub = z

    for i in range(1,k):
        # sum y's to get x
        # sum x's to get y
        return

# how many hubs point to me
# def getNewAuthWeight(xAuth: list,):




def main():
    print("query:", end=" ")
    query = input()

    (base_set, links) = tf_idf.getCandiadatePages(query)
    print(base_set)
    # print(links[0])
    linkMap = makeLinkMap(links=links)
    print(linkMap)
    # iterate(base_set=base_set, k=20)
# 

if __name__ == "__main__":
    main()

