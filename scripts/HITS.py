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


def generateIndexMap(baseSet: dict) -> dict[dict[int, list[int]]]:
    indexMap = {}

    for (key, values) in baseSet.items():
        if key not in indexMap:
            indexMap[key] = {I_POINT_TO_WHO: [], WHO_POINTS_TO_ME: []}

        indexMap[key][I_POINT_TO_WHO] = values

        for val in values:
            if val not in indexMap:
                indexMap[val] = {I_POINT_TO_WHO: [], WHO_POINTS_TO_ME: []}

            indexMap[val][WHO_POINTS_TO_ME].append(key)

    return indexMap

def getNewWeights(index_map: dict, hits_index: dict, updateArr: list, fetchArr: list, update_x: bool):
    for (key, obj) in index_map.items():
        update_type = WHO_POINTS_TO_ME if update_x else I_POINT_TO_WHO
        curr_index = hits_index[key]
        new_val = 0
        for val in obj[update_type]:
            new_val += fetchArr[hits_index[val]]
        
        updateArr[curr_index] = new_val
    
    update_sum = sum(updateArr)
    updateArr = [val / update_sum for val in updateArr]
    
    return updateArr


def iterate(base_set: list, k: int):
    hits_index = {key: i for i, key in enumerate(base_set.keys())}
    index_map = generateIndexMap(base_set)

    xAuth = [1] * len(base_set)
    yHub = [1] * len(base_set)

    for _ in range(0, k):
        xAuth = getNewWeights(index_map, hits_index, xAuth, yHub, True)
        yHub = getNewWeights(index_map, hits_index, yHub, xAuth, False)
    
    return xAuth, yHub
        
        

# how many hubs point to me
# def getNewAuthWeight(xAuth: list,):




def main():
    data = {
    201: [],
    202: [201, 211],
    203: [201, 209, 210],
    204: [201, 205, 206, 211, 212],
    205: [201, 206, 207],
    206: [201, 204],
    207: [201, 205],
    208: [201, 203, 207, 210],
    209: [201, 203],
    210: [201, 203],
    211: [201, 204, 206],
    212: [201]
  }


    # print("query:", end=" ")
    # query = input()

    # (base_set, links) = tf_idf.getCandiadatePages(query)
    # print(base_set)
    # print(links[0])
    # linkMap = makeLinkMap(links=links)
    # print(linkMap)
    xAuth, yHub = iterate(base_set=data, k=20)
    print(xAuth)
    print(yHub)

    xAuth_winner = xAuth.index(max(xAuth))
    yHub_winner = yHub.index(max(yHub))

    print("\n" * 10)
    print(xAuth_winner)
    print(yHub_winner)
#

if __name__ == "__main__":
    main()

