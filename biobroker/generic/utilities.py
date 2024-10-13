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


def parse_pydantic_errors(pydantic_errors: list[dict]) -> list:
    messages = []
    for error in pydantic_errors:
        location = "-->".join([str(e) for e in error['loc']]) if error['loc'] else "root"
        user_input = error['input']
        match error['type']:
            case 'model_type':
                message = "Value provided should be a dictionary"
            case 'string_pattern_mismatch':
                message = f"Value provided must match pattern {error['ctx']['pattern']}"
            case 'missing':
                message = f"Missing mandatory field '{error['loc'][-1]}'"
                location = "-->".join([str(e) for e in error['loc']][:-1]) if len(error['loc']) > 1 else "root"
            case _:
                message = error['msg']
        messages.append(f"{location}: {message}. Provided value: '{user_input}'")
    return messages