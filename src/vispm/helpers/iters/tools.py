
from typing import Iterable

def iter_chunker(iter:Iterable, chunk_size:int):
    start = 0 
    end = chunk_size
    iter_len = len(iter)
    while start < iter_len:
        yield iter[start:end]
        start = end 
        end = end + chunk_size