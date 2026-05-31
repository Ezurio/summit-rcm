#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Helpers for serial-port setup used by the AT interface."""

import asyncio
import ctypes
import errno
import fcntl
import os
import termios

import serial_asyncio


class SerialStruct(ctypes.Structure):
    """Linux serial_struct layout for TIOCGSERIAL/TIOCSSERIAL ioctls."""

    _fields_ = [
        ("type", ctypes.c_int),
        ("line", ctypes.c_int),
        ("port", ctypes.c_uint),
        ("irq", ctypes.c_int),
        ("flags", ctypes.c_int),
        ("xmit_fifo_size", ctypes.c_int),
        ("custom_divisor", ctypes.c_int),
        ("baud_base", ctypes.c_int),
        ("close_delay", ctypes.c_ushort),
        ("io_type", ctypes.c_ubyte),
        ("reserved_char", ctypes.c_ubyte),
        ("hub6", ctypes.c_int),
        ("closing_wait", ctypes.c_ushort),
        ("closing_wait2", ctypes.c_ushort),
        ("iomem_base", ctypes.c_void_p),
        ("iomem_reg_shift", ctypes.c_ushort),
        ("port_high", ctypes.c_uint),
        ("iomap_base", ctypes.c_ulong),
    ]


def _supports_serial_struct(error: OSError) -> bool:
    unsupported_errnos = {
        errno.ENOTTY,
        errno.EINVAL,
        errno.EOPNOTSUPP,
    }
    enoioctlcmd = getattr(errno, "ENOIOCTLCMD", None)
    if enoioctlcmd is not None:
        unsupported_errnos.add(enoioctlcmd)
    return error.errno not in unsupported_errnos


def set_closing_wait(serial_port: str, closing_wait_in: int = 65535) -> bool:
    """
    Best-effort serial closing-wait configuration.

    Applies UART-specific `serial_struct` settings when supported and returns whether
    the closing-wait setting was actually applied. PTYs and other tty-like devices that
    don't support these ioctls are treated as a no-op.
    """
    if not serial_port:
        raise ValueError("AT Interface Failed: Invalid Serial Port")

    if closing_wait_in < 0 or closing_wait_in > 65535:
        raise ValueError("AT Interface Failed: Invalid Closing Wait Time")

    fd: int | None = None

    try:
        fd = os.open(serial_port, os.O_RDWR | os.O_NOCTTY)
        serial_info = SerialStruct()
        try:
            fcntl.ioctl(fd, termios.TIOCGSERIAL, serial_info)
        except OSError as error:
            if _supports_serial_struct(error):
                raise
            return False

        serial_info.closing_wait = closing_wait_in
        try:
            fcntl.ioctl(fd, termios.TIOCSSERIAL, serial_info)
        except OSError as error:
            if _supports_serial_struct(error):
                raise
            return False

        return True
    finally:
        if fd is not None:
            os.close(fd)


async def create_serial_connection(
    loop: asyncio.AbstractEventLoop,
    protocol_factory,
    serial_port: str,
    baud_rate: int,
    *,
    rtscts: bool = True,
):
    """Open an asyncio serial connection after any caller-specific setup."""
    return await serial_asyncio.create_serial_connection(
        loop,
        protocol_factory,
        serial_port,
        baud_rate,
        rtscts=rtscts,
    )