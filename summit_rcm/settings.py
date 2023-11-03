import os
import configparser
from syslog import LOG_ERR, syslog
from typing import Optional

from summit_rcm.utils import Singleton
from summit_rcm import definition
from threading import Lock


"""
    Summit RCM system settings manage based on configParser
"""


class SummitRCMConfigManage(object):
    """
    summit-rcm.ini has multi sections:
    1. Each user has a section with username as the section name;
    2. Other system settings should be saved in 'settings' section;
    """

    _lock = Lock()
    _parser = configparser.ConfigParser(defaults=None)
    _filename = definition.SUMMIT_RCM_SETTINGS_FILE
    if os.path.isfile(_filename):
        _parser.read(_filename)

    @classmethod
    def verify_section(cls, section):
        with cls._lock:
            if cls._parser.has_section(section):
                return True
        return False

    @classmethod
    def add_section(cls, section):
        with cls._lock:
            if not cls._parser.has_section(section):
                cls._parser.add_section(section)
                return True
        return False

    @classmethod
    def remove_section(cls, section):
        with cls._lock:
            if cls._parser.has_section(section):
                cls._parser.remove_section(section)
                return True
        return False

    @classmethod
    def update_key_from_section(cls, section, key, val):
        with cls._lock:
            if cls._parser.has_section(section):
                cls._parser.set(section, key, val)
                return True
        return False

    @classmethod
    def get_key_from_section(cls, section, key, fallback=None):
        if cls._parser.has_section(section):
            return cls._parser.get(section, key, fallback=fallback)
        return fallback

    @classmethod
    def get_bool_key_from_section(cls, section, key, fallback=None):
        if cls._parser.has_section(section):
            return cls._parser.getboolean(section, key, fallback=fallback)
        return fallback

    @classmethod
    def delete_key_from_section(cls, section, key):
        with cls._lock:
            if cls._parser.has_section(section):
                cls._parser.remove_option(section, key)

    @classmethod
    def get_section_size_by_key(cls, key):
        cnt = 0
        with cls._lock:
            for k in cls._parser.sections():
                if cls._parser.get(k, key, fallback=None):
                    cnt += 1
        return cnt

    @classmethod
    def get_sections_by_key(cls, key):
        result = []
        with cls._lock:
            for k in cls._parser.sections():
                if cls._parser.get(k, key, fallback=None):
                    result.append(k)
        return result

    @classmethod
    def get_sections_and_key(cls, key):
        result = {}
        with cls._lock:
            for k in cls._parser.sections():
                if cls._parser.get(k, key, fallback=None):
                    result[k] = cls._parser.get(k, key)
        return result

    @classmethod
    def save(cls):
        with cls._lock:
            with open(cls._filename, "w") as fp:
                cls._parser.write(fp)
                return True
        return False


class SystemSettingsManage(object):
    """Manage 'settings' section"""

    section = "settings"
    __initialized = False

    @classmethod
    def check_init(cls):
        if not cls.__initialized:
            cls.__initialized = True
            cls.initialize()

    @classmethod
    def initialize(cls):
        return SummitRCMConfigManage.add_section(cls.section)

    @classmethod
    def update(cls, key, val):
        cls.check_init()
        return SummitRCMConfigManage.update_key_from_section(cls.section, key, val)

    @classmethod
    def get(cls, key, fallback=None):
        return SummitRCMConfigManage.get_key_from_section(cls.section, key, fallback)

    @classmethod
    def getInt(cls, key, fallback=None):
        return int(
            SummitRCMConfigManage.get_key_from_section(cls.section, key, fallback)
        )

    @classmethod
    def getBool(cls, key, fallback=None):
        value = SummitRCMConfigManage.get_bool_key_from_section(
            cls.section, key, fallback
        )
        return value

    @classmethod
    def update_persistent(cls, key, val):
        cls.check_init()
        return (
            SummitRCMConfigManage.update_key_from_section(cls.section, key, val)
            and SummitRCMConfigManage.save()
        )

    @classmethod
    def delete(cls, key):
        return SummitRCMConfigManage.delete_key_from_section(cls.section, key)

    @classmethod
    def delete_persistent(cls, key):
        SummitRCMConfigManage.delete_key_from_section(cls.section, key)
        return SummitRCMConfigManage.save()

    @classmethod
    def save(cls):
        return SummitRCMConfigManage.save()

    @classmethod
    def get_session_timeout(cls):
        "Unit: Minute"
        return int(
            SummitRCMConfigManage.get_key_from_section(
                cls.section, "session_timeout", 10
            )
        )

    @classmethod
    def get_tamper_protection_timeout(cls):
        "Unit: Second"
        return int(
            SummitRCMConfigManage.get_key_from_section(
                cls.section, "tamper_protection_timeout", 600
            )
        )

    @classmethod
    def get_max_web_clients(cls):
        return int(
            SummitRCMConfigManage.get_key_from_section(
                cls.section, "max_web_clients", 1
            )
        )

    @classmethod
    def get_user_callback_timeout(cls):
        "Unit: Second"
        return int(
            SummitRCMConfigManage.get_key_from_section(
                cls.section, "user_callback_timeout", 10
            )
        )

    @classmethod
    def get_login_retry_times(cls):
        return int(
            SummitRCMConfigManage.get_key_from_section(
                cls.section, "login_retry_times", 5
            )
        )

    @classmethod
    def get_login_retry_window(cls):
        return int(
            SummitRCMConfigManage.get_key_from_section(
                cls.section, "login_retry_window", 600
            )
        )

    @classmethod
    def get_log_data_streaming_size(cls):
        return int(
            SummitRCMConfigManage.get_key_from_section(
                cls.section, "log_data_streaming_size", 100
            )
        )

    @classmethod
    def get_cert_for_file_encryption(cls):
        return SummitRCMConfigManage.get_key_from_section(
            cls.section,
            "cert_for_file_encryption",
            "/etc/summit-rcm/ssl/server.crt",
        )


class ServerConfig(object, metaclass=Singleton):
    def __init__(self):
        try:
            self.parser = configparser.ConfigParser()
            self.parser.read(definition.SUMMIT_RCM_SERVER_CONF_FILE)

            self._sessions_enabled = self.parser.getboolean(
                section="/", option="tools.session.on", fallback=True
            )
            self._validate_request = self.parser.getboolean(
                section="summit-rcm", option="rest_api_validate_request", fallback=False
            )
            self._validate_response = self.parser.getboolean(
                section="summit-rcm",
                option="rest_api_validate_response",
                fallback=False,
            )
            self._rest_api_docs_enabled = self.parser.getboolean(
                section="summit-rcm", option="rest_api_docs", fallback=False
            ) or os.environ.get("DOCS_GENERATION", "False") == "True"
        except Exception:
            syslog(LOG_ERR, "Unable to parse server configuration")
            self.parser = None
            self._sessions_enabled = True
            self._validate_request = False
            self._validate_response = False
            self._rest_api_docs_enabled = False

    def get_parser(self) -> Optional[configparser.ConfigParser]:
        return self.parser

    @property
    def sessions_enabled(self) -> bool:
        """Determine whether or not cookie-based sessions are enabled"""
        return self._sessions_enabled

    @property
    def rest_api_docs_enabled(self) -> bool:
        """Determine whether or not the REST API documentation is enabled"""
        return self._rest_api_docs_enabled

    @property
    def validate_request(self) -> bool:
        """Determine whether or not request validation is enabled"""
        return self._validate_request

    @property
    def validate_response(self) -> bool:
        """Determine whether or not response validation is enabled"""
        return self._validate_response
