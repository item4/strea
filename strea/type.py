import inspect
from types import SimpleNamespace
from typing import (
    Any,
    Dict,
    Mapping,
    MutableSequence,
    Sequence,
    Union,
)


class Namespace(SimpleNamespace):
    """Typed Namespace."""

    def __init__(self, **kwargs) -> None:
        for k, t in self.__annotations__.items():
            kwargs[k] = cast(t, kwargs.get(k))

        super(Namespace, self).__init__(**kwargs)


NoneType = type(None)
UnionType = type(Union)


def cast(t, value):
    """Magical casting."""

    if type(t) == UnionType:
        for ty in t.__args__:
            try:
                return cast(ty, value)
            except:  # noqa: E722
                continue
        raise ValueError()
    elif t == Any:
        return value
    elif t == NoneType:
        return None
    elif t in (str, bytes):
        return t(value)

    if inspect.isclass(t):
        if issubclass(t, Namespace):
            return t(**value)

        if issubclass(t, tuple):
            if t.__args__:
                return tuple(cast(ty, x) for ty, x in zip(t.__args__, value))
            else:
                return tuple(value)

        if issubclass(t, set):
            if t.__args__:
                return {cast(t.__args__[0], x) for x in value}
            else:
                return set(value)

        if issubclass(t, (list, MutableSequence, Sequence)):
            if t.__args__:
                return [cast(t.__args__[0], x) for x in value]
            else:
                return list(value)

        if issubclass(t, (Dict, Mapping)):
            if t.__args__:
                return {
                    cast(t.__args__[0], k): cast(t.__args__[1], v)
                    for k, v in value.items()
                }
            else:
                return dict(value)

    return t(value)


def is_container(t) -> bool:
    """Check given value is container type?"""

    return any(issubclass(t, x) for x in [set, tuple, list])
