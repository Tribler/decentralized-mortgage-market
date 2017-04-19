def median(lst):
    sorted_lst = sorted(lst)
    half, odd = divmod(len(sorted_lst), 2)
    if odd:
        return sorted_lst[half]
    return (sorted_lst[half - 1] + sorted_lst[half]) / 2.
