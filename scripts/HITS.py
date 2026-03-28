import tf_idf as tf_idf
from db import Database

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



def getNewWeights(index_map: dict, hits_index: dict, mult: dict, updateArr: list, fetchArr: list, update_x: bool):
    for (key, obj) in index_map.items():
        update_type = WHO_POINTS_TO_ME if update_x else I_POINT_TO_WHO
        curr_index = hits_index[key]
        curr_mult = mult.get(key, 0.5)
        new_val= 0
        for val in obj[update_type]:
            val_mult = mult.get(val, 0.5)
            new_val += fetchArr[hits_index[val]] * val_mult * curr_mult

        updateArr[curr_index] = new_val

    update_sum = sum(updateArr)
    updateArr = [val / update_sum for val in updateArr]

    return updateArr



def iterate(base_set: list, mult: dict, k: int):
    hits_index = {key: i for i, key in enumerate(base_set.keys())}
    index_map = generateIndexMap(base_set)

    xAuth = [1.0] * len(base_set)
    yHub = [1.0] * len(base_set)

    for _ in range(0, k):
        xAuth = getNewWeights(index_map, hits_index, mult, xAuth, yHub, True)
        yHub = getNewWeights(index_map, hits_index, mult, yHub, xAuth, False)

    reverse_hits_index = {i: key for key, i in hits_index.items()}
    x_tuple = []
    y_tuple = []
    for i, (x_val, y_val) in enumerate(zip(xAuth, yHub)):
        x_tuple.append((reverse_hits_index[i], x_val))
        y_tuple.append((reverse_hits_index[i], y_val))

    return x_tuple, y_tuple




def main():
    query = input("query: ")

    base_set, tf_idf_mult = tf_idf.getCandiadatePages(query)

    xAuth, yHub = iterate(base_set=base_set, mult=tf_idf_mult, k=3)

    top_x = sorted(xAuth, key=lambda x: x[1], reverse=True)[:20]
    top_y = sorted(yHub, key=lambda x: x[1], reverse=True)[:20]

    auth_ids_str = ",".join(str(doc_id) for doc_id, _ in top_x)
    auth_query = f"SELECT doc_id, page_name FROM DOCUMENTS WHERE doc_id IN ({auth_ids_str})"
    
    hub_ids_str = ",".join(str(doc_id) for doc_id, _ in top_y)
    hub_query = f"SELECT doc_id, page_name FROM DOCUMENTS WHERE doc_id IN ({hub_ids_str})"

    db = Database()
    
    print("\n--- TOP AUTHORITIES (Answers) ---")
    for val in db.executeQuery(auth_query): {
        print(val[1])
    }

    print("\n--- TOP HUBS (Directories) ---")
    for val in db.executeQuery(hub_query): {
        print(val[1])
    }


if __name__ == "__main__":
    main()

