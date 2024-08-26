#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to support Chrony NTP configuration
"""

import os
from syslog import syslog, LOG_ERR
from typing import List
import asyncio
try:
    import aiofiles
except ImportError as error:
    # Ignore the error if the aiofiles module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error

ADD_SOURCE = "addSource"
REMOVE_SOURCE = "removeSource"
OVERRIDE_SOURCES = "overrideSources"
SOURCE_COMMANDS = [ADD_SOURCE, REMOVE_SOURCE, OVERRIDE_SOURCES]
CHRONY_SOURCES_PATH = "/etc/chrony/supplemental.sources"
CHRONYC_PATH = "/usr/bin/chronyc"


class ChronyNTPService:
    """
    Manages chrony NTP configuration
    """

    @staticmethod
    async def chrony_reload_sources() -> bool:
        """
        Trigger chrony to reload sources.
        Returns True for success and False for failure.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                *[CHRONYC_PATH, "reload", "sources"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            # When successful, 'chronyc reload sources' returns '200 OK' to stdout
            if "OK" in stdout.decode("utf-8"):
                return True

            raise Exception(stderr.decode("utf-8"))
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Error reloading chrony sources - {str(exception)}",
            )
            return False

    @staticmethod
    async def chrony_get_static_sources() -> List[str]:
        """
        Retrieve chrony sources configured by Summit RCM (static)
        """

        sources = []

        if os.path.exists(CHRONY_SOURCES_PATH):
            async with aiofiles.open(CHRONY_SOURCES_PATH, "r") as chrony_sources:
                for line in await chrony_sources.readlines():
                    line = line.strip()

                    # Ignore commented out lines
                    if line.startswith("#"):
                        continue

                    if line.startswith("server"):
                        source_config = line.split(" ")[1:]
                        if len(source_config) < 1:
                            continue

                        sources.append(source_config[0])

        return sources

    @staticmethod
    async def chrony_get_current_sources() -> List[str]:
        """
        Retrieve all chrony sources as reported by chronyc
        """
        sources = []

        # Run 'chronyc -c -N sources'
        # -c triggers chronyc to enable CSV format
        # -N triggers chronyc to print original source names
        proc = await asyncio.create_subprocess_exec(
            *[CHRONYC_PATH, "-c", "-N", "sources"],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        sources_csv_lines = stdout.decode("utf-8").splitlines()
        for line in sources_csv_lines:
            # The source name is the 3rd parameter
            # Example ouput from 'chronyc -c -N sources':
            # ^,?,time.nist.gov,1,6,1,26,-1468274.750000000,-1468274.750000000,0.034612902
            csv_data = line.split(",")
            if len(csv_data) < 3:
                continue
            sources.append(csv_data[2])

        return sources

    @staticmethod
    async def chrony_get_sources() -> List[dict]:
        """
        Retrieve all chrony sources
        """
        sources = []

        static_sources = await ChronyNTPService.chrony_get_static_sources()

        for static_source in static_sources:
            sources.append({"address": static_source, "type": "static"})

        for source in await ChronyNTPService.chrony_get_current_sources():
            # Since the 'current' sources includes the sources configured 'statically', only append
            # the ones that are not already set 'statically'
            if source not in static_sources:
                sources.append({"address": source, "type": "dynamic"})

        return sources

    @staticmethod
    async def chrony_configure_sources(command: str, sources_in: List[str]) -> None:
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
        if command == ADD_SOURCE:
            current_sources = await ChronyNTPService.chrony_get_static_sources()

            # Add back any current sources
            for source in current_sources:
                new_sources.append(source)

            # Append any new source from 'sources_in' that isn't already set
            for source in sources_in:
                if source not in current_sources:
                    new_sources.append(source)
        elif command == REMOVE_SOURCE:
            # Only add back any sources that aren't in 'sources_in'
            for source in await ChronyNTPService.chrony_get_static_sources():
                if source not in sources_in:
                    new_sources.append(source)
        elif command == OVERRIDE_SOURCES:
            # Simply use the new list of sources
            new_sources = sources_in

        new_sources_lines = []
        for source in new_sources:
            new_sources_lines.append(f"server {source}\n")

        async with aiofiles.open(CHRONY_SOURCES_PATH, "w") as chrony_sources:
            for line in new_sources_lines:
                await chrony_sources.write(line)

        await ChronyNTPService.chrony_reload_sources()
