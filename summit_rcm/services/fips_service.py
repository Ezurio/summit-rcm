from subprocess import CalledProcessError, run
from syslog import LOG_ERR, syslog
from summit_rcm.utils import Singleton

VALID_FIPS_STATES = ["fips", "fips_wifi", "unset"]
FIPS_SCRIPT = "/usr/bin/fips-set"


class FipsService(metaclass=Singleton):
    async def set_fips_state(self, value: str) -> bool:
        """
        Configure the desired FIPS state for the module (reboot required) and return a boolean
        indicating success. Possible values are:
        - fips
        - fips_wifi
        - unset
        """
        success = False
        try:
            if value not in ["fips", "fips_wifi", "unset"]:
                raise f"invalid input parameter {str(value)}"

            run(
                [FIPS_SCRIPT, value],
                check=True,
            )
            success = True
        except FileNotFoundError:
            pass
        except CalledProcessError as e:
            syslog(LOG_ERR, f"set_fips_state error: {str(e.returncode)}")
        except Exception as e:
            syslog(LOG_ERR, f"set_fips_state exception: {str(e)}")
        return success

    async def get_fips_state(self) -> str:
        """
        Retrieve the current FIPS state for the module. Possible values are:
        - fips
        - fips_wifi
        - unset
        - unsupported
        - unknown
        """
        try:
            p = run(
                [FIPS_SCRIPT, "status"],
                capture_output=True,
                check=True,
            )
            status = p.stdout.decode("utf-8").strip()
            return status if status in VALID_FIPS_STATES else "unknown"
        except FileNotFoundError:
            return "unsupported"
        except CalledProcessError as e:
            syslog(LOG_ERR, f"get_fips_state error: {str(e.returncode)}")
            return "unknown"
        except Exception as e:
            syslog(LOG_ERR, f"get_fips_state exception: {str(e)}")
            return "unknown"
