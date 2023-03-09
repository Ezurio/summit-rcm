import os
from syslog import syslog, LOG_ERR
from subprocess import run
import falcon
from typing import List
from ..definition import SUMMIT_RCM_ERRORS


ADD_SOURCE = "addSource"
REMOVE_SOURCE = "removeSource"
SOURCE_COMMANDS = [ADD_SOURCE, REMOVE_SOURCE]
NTP_GET_MAX_PATH_DEPTH = 2
NTP_PUT_MAX_PATH_DEPTH = 3


class NTP(object):
    """
    Manages chrony NTP configuration
    """

    CHRONY_SOURCES_PATH = "/etc/chrony/supplemental.sources"
    CHRONYC_PATH = "/usr/bin/chronyc"

    def chrony_reload_sources(self) -> bool:
        """
        Trigger chrony to reload sources.
        Returns True for success and False for failure.
        """
        try:
            p = run(
                [self.CHRONYC_PATH, "reload", "sources"],
                capture_output=True,
                check=True,
            )

            # When successful, 'chronyc reload sources' returns '200 OK' to stdout
            return "OK" in p.stdout.decode("utf-8")
        except Exception as e:
            syslog(LOG_ERR, f"Error reloading chrony sources - {str(e)}")
            return False

    def chrony_get_static_sources(self) -> List[str]:
        """
        Retrieve chrony sources configured by Summit RCM (static)
        """

        sources = []

        if os.path.exists(self.CHRONY_SOURCES_PATH):
            with open(self.CHRONY_SOURCES_PATH, "r") as chrony_sources:
                for line in chrony_sources.readlines():
                    line = line.strip()

                    # Ignore commented out lines
                    if line.startswith("#"):
                        continue

                    if line.startswith("server"):
                        source_config = line.split(" ")[1:]
                        if len(source_config) < 1:
                            return

                        sources.append(source_config[0])

        return sources

    def chrony_get_current_sources(self) -> List[str]:
        """
        Retrieve all chrony sources as reported by chronyc
        """
        sources = []

        # Run 'chronyc -c -N sources'
        # -c triggers chronyc to enable CSV format
        # -N triggers chronyc to print original source names
        p = run(
            [self.CHRONYC_PATH, "-c", "-N", "sources"],
            capture_output=True,
            check=True,
        )

        sources_csv_lines = p.stdout.decode("utf-8").splitlines()
        for line in sources_csv_lines:
            # The source name is the 3rd parameter
            # Example ouput from 'chronyc -c -N sources':
            # ^,?,time.nist.gov,1,6,1,26,-1468274.750000000,-1468274.750000000,0.034612902
            csv_data = line.split(",")
            if len(csv_data) < 3:
                continue
            sources.append(csv_data[2])

        return sources

    def chrony_get_sources(self) -> list:
        """
        Retrieve all chrony sources
        """
        sources = []

        static_sources = self.chrony_get_static_sources()

        for static_source in static_sources:
            sources.append({"address": static_source, "type": "static"})

        for source in self.chrony_get_current_sources():
            # Since the 'current' sources includes the sources configured 'statically', only append
            # the ones that are not already set 'statically'
            if source not in static_sources:
                sources.append({"address": source, "type": "dynamic"})

        return sources

    def chrony_configure_sources(self, command: str, sources_in: List[str]) -> None:
        """
        Reconfigure the Summit RCM chrony sources

        The 'command' input parameter controls whether the incoming 'sources_in' list is added or
        removed from the current list of static sources.

        The 'sources_in' input parameter is expected to be list of addresses as strings to add or
        remove. For example:
        [
            "time.nist.gov",
            "1.2.3.4"
        ]
        """
        if command not in SOURCE_COMMANDS:
            raise Exception("Invalid command")

        new_sources = []
        current_sources = self.chrony_get_static_sources()
        if command == ADD_SOURCE:
            # Add back any current sources
            for source in current_sources:
                new_sources.append(source)

            # Append any new source from 'sources_in' that isn't already set
            for source in sources_in:
                if source not in current_sources:
                    new_sources.append(source)
        elif command == REMOVE_SOURCE:
            # Only add back any sources that aren't in 'sources_in'
            for source in current_sources:
                if source not in sources_in:
                    new_sources.append(source)

        new_sources_lines = []
        for source in new_sources:
            new_sources_lines.append(f"server {source}\n")

        with open(self.CHRONY_SOURCES_PATH, "w") as chrony_sources:
            for line in new_sources_lines:
                chrony_sources.write(line)

        self.chrony_reload_sources()

    @staticmethod
    def result_parameter_not_one_of(parameter: str, supplied_value: str, not_one_of):
        """
        Generate return object value for when a supplied value is not valid
        """
        return {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": f"supplied parameter '{parameter}' value {supplied_value} must be one of"
            f" {not_one_of}, ",
        }

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            result["sources"] = self.chrony_get_sources()
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result["sources"] = []
            result["InfoMsg"] = f"Unable to retrieve chrony sources - {str(e)}"
        resp.media = result

    async def on_put(self, req, resp, command):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            post_data = await req.get_media()

            if command:
                if command not in SOURCE_COMMANDS:
                    result.update(
                        self.result_parameter_not_one_of(
                            "command", command, SOURCE_COMMANDS
                        )
                    )
                else:
                    self.chrony_configure_sources(command, post_data.get("sources", []))
                    result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            else:
                result["InfoMsg"] = "No command specified"
        except Exception as e:
            result["InfoMsg"] = f"Unable to update chrony sources - {str(e)}"

        resp.media = result
