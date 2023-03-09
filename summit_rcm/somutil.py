from pathlib import Path

CMDLINE_BOOTSIDE_A = "ubi.block=0,1"
CMDLINE_BOOTSIDE_B = "ubi.block=0,4"


def get_current_side():
    """
    Return the current bootside
    """
    cmdline = Path("/proc/cmdline").read_text()
    if CMDLINE_BOOTSIDE_B in cmdline:
        return "b"
    elif CMDLINE_BOOTSIDE_A in cmdline:
        return "a"
    else:
        raise ValueError(
            "get_current_side: could not determine boot side from kernel cmdline"
        )
