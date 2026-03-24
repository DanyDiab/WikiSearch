# import tf_idf as tf_idf
I_POINT_TO_WHO = 0
WHO_POINTS_TO_ME = 1
def makeLinkMap(links: list) -> map:
    linkMap = {}
    for doc_id, link_id in links:
        if doc_id not in linkMap:
            linkMap[doc_id] = set()
        linkMap[doc_id].add(link_id)
    return linkMap


def generateIndexMap(baseSet: dict):
    
    adjMatrix = [
        [0] * len(baseSet) for i in range(len(baseSet))
    ]


    indexMap = {}

    for (key, values) in baseSet.items():
        if key not in indexMap:
            indexMap[key] = {I_POINT_TO_WHO: [], WHO_POINTS_TO_ME: []}
        
        indexMap[key][I_POINT_TO_WHO] = values 

        for val in values:
            if val not in indexMap:
                indexMap[val] = {I_POINT_TO_WHO: [], WHO_POINTS_TO_ME: []}
            
            indexMap[val][WHO_POINTS_TO_ME].append(key)
    
    return adjMatrix

def getNewWeights(valArr: dict, index_map: dict, updateArr: list, fetchArr: list):
    for (key,valArr) in valArr:
        for val in valArr:
            pass

def iterate(base_set: list, k: int):
    index_map = {}

    for i, key in enumerate(base_set.keys()):
        index_map[key] = i
    
    generateIndexMap(base_set)
    return
    z = [1] * len(base_set)
    xAuth = z
    yHub = z

    for i in range(0,k):
        # xAuth = 
        # sum y's to get x
        # sum x's to get y
        return

# how many hubs point to me
# def getNewAuthWeight(xAuth: list,):




def main():
    data = {
        101: [102, 103, 104],
        102: [101],
        103: [101, 104],
        104: [101, 105],
        105: [101, 106],
        106: [101, 103]
    }

    
    # print("query:", end=" ")
    # query = input()

    # (base_set, links) = tf_idf.getCandiadatePages(query)
    # print(base_set)
    # print(links[0])
    # linkMap = makeLinkMap(links=links)
    # print(linkMap)
    iterate(base_set=data, k=20)
# 

if __name__ == "__main__":
    main()

