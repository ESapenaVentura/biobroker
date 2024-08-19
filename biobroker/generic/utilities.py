from typing import Generator


def slice_list(list_to_chunk: list | tuple, chunk_size: int) -> Generator:
    """
    Slice an iterable (List/Tuple) returning tuples of 'chunk_sixe' size.

    :param list_to_chunk: iterable to slice
    :param chunk_size: Size of the chunk
    :return: Generator of 'chunk_size' sizes of the list.
    """
    n = max(1, chunk_size)
    return (list_to_chunk[i:i+n] for i in range(0, len(list_to_chunk), n))