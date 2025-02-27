from __future__ import annotations

import sys
import ctypes
from io import BufferedRandom, BufferedReader, BufferedWriter, FileIO, TextIOWrapper
from os import F_OK, R_OK, W_OK, X_OK, access, path, getenv
from pathlib import Path
from typing import IO, Any, BinaryIO, Literal, overload

from ..exceptions import FileIsADirectoryError, FileNotExistsError, FilePermissionError, FileWasNotFoundError
from ..types import (
    FileOpener, FilePathType, FuncExceptT, OpenBinaryMode, OpenBinaryModeReading, OpenBinaryModeUpdating,
    OpenBinaryModeWriting, OpenTextMode
)

__all__ = [
    'get_user_data_dir',

    'check_perms',
    'open_file'
]


def get_user_data_dir() -> Path:
    if sys.platform == 'win32':
        buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.shell32.SHGetFolderPathW(None, 28, None, 0, buf)

        if any([ord(c) > 255 for c in buf]):
            buf2 = ctypes.create_unicode_buffer(1024)
            if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
                buf = buf2

        return Path(path.normpath(buf.value))

    if sys.platform == 'darwin':  # type: ignore[unreachable]
        return Path(path.expanduser('~/Library/Application Support/'))

    return Path(getenv('XDG_DATA_HOME', path.expanduser("~/.local/share")))


def check_perms(
    file: FilePathType, mode: OpenTextMode | OpenBinaryMode, *, func: FuncExceptT | None = None
) -> bool:
    file = Path(str(file))
    got_perms = False

    mode_i = F_OK

    if func is not None:
        if not str(file):
            raise FileNotExistsError(file, func)

    for char in 'rbU':
        mode_str = mode.replace(char, '')

    if file.is_file():
        if not mode_str:
            mode_i = R_OK
        elif 'x' in mode_str:
            mode_i = X_OK
        elif '+' in mode_str or 'w' in mode_str:
            mode_i = W_OK

        got_perms = access(file, mode_i)

    if func is not None:
        if not got_perms:
            raise FilePermissionError(file, func)
        elif file.is_dir():
            raise FileIsADirectoryError(file, func)
        elif not file.exists():
            if file.parent.exists():
                raise FileWasNotFoundError(file, func)
            else:
                raise FileNotExistsError(file, func)

    return got_perms


@overload
def open_file(
    file: FilePathType, mode: OpenTextMode = 'r', buffering: int = ...,
    encoding: str | None = None, errors: str | None = ..., newline: str | None = ...,
    *, func: FuncExceptT | None = None
) -> TextIOWrapper:
    ...


@overload
def open_file(
    file: FilePathType, mode: OpenBinaryMode, buffering: Literal[0],
    encoding: None = None, *, func: FuncExceptT | None = None
) -> FileIO:
    ...


@overload
def open_file(
    file: FilePathType, mode: OpenBinaryModeUpdating, buffering: Literal[-1, 1] = ...,
    encoding: None = None, *, func: FuncExceptT | None = None
) -> BufferedRandom:
    ...


@overload
def open_file(
    file: FilePathType, mode: OpenBinaryModeWriting, buffering: Literal[-1, 1] = ...,
    encoding: None = None, *, func: FuncExceptT | None = None
) -> BufferedWriter:
    ...


@overload
def open_file(
    file: FilePathType, mode: OpenBinaryModeReading, buffering: Literal[-1, 1] = ...,
    encoding: None = None, *, func: FuncExceptT | None = None
) -> BufferedReader:
    ...


@overload
def open_file(
    file: FilePathType, mode: OpenBinaryMode, buffering: int = ...,
    encoding: None = None, *, func: FuncExceptT | None = None
) -> BinaryIO:
    ...


@overload
def open_file(
    file: FilePathType, mode: str, buffering: int = ...,
    encoding: str | None = ..., errors: str | None = ..., newline: str | None = ...,
    closefd: bool = ..., opener: FileOpener | None = ..., *, func: FuncExceptT | None = None
) -> IO[Any]:
    ...


def open_file(file: FilePathType, mode: Any = 'r+', *args: Any, func: FuncExceptT | None = None, **kwargs: Any) -> Any:
    check_perms(file, mode, func=func)
    return open(file, mode, *args, errors='strict', closefd=True, **kwargs)  # type: ignore
