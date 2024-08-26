#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle user management interactions
"""

import hashlib
import uuid
from summit_rcm.settings import (
    ServerConfig,
    SummitRCMConfigManage,
    SystemSettingsManage,
)
from summit_rcm.utils import Singleton


class UserService(metaclass=Singleton):
    """Service to handle user management"""

    @staticmethod
    def verify(username: str, password: str) -> bool:
        """Verify the provided username and password are correct"""

        key = SummitRCMConfigManage.get_key_from_section(username, "salt")
        if not key:
            return False

        attempt = hashlib.sha256(key.encode() + password.encode()).hexdigest()
        return attempt == SummitRCMConfigManage.get_key_from_section(
            username, "password", None
        )

    @staticmethod
    def user_exists(username: str) -> bool:
        """Retrieve whether or not the provided username exists"""

        return SummitRCMConfigManage.verify_section(username)

    @staticmethod
    def delete_user(username: str) -> bool:
        """Delete the user with the specified username"""

        if SummitRCMConfigManage.remove_section(username):
            return SummitRCMConfigManage.save()
        return False

    @staticmethod
    def add_user(username: str, password: str, permission: str = None) -> bool:
        """Add a new user with the specified username, password, and permissions"""

        if SummitRCMConfigManage.add_section(username):
            salt = uuid.uuid4().hex
            SummitRCMConfigManage.update_key_from_section(username, "salt", salt)
            SummitRCMConfigManage.update_key_from_section(
                username,
                "password",
                hashlib.sha256(salt.encode() + password.encode()).hexdigest(),
            )
            if permission:
                SummitRCMConfigManage.update_key_from_section(
                    username, "permission", permission
                )
            return SummitRCMConfigManage.save()
        return False

    @staticmethod
    def update_password(username: str, password: str) -> bool:
        """Update the password for the user with the specified username"""

        if SummitRCMConfigManage.get_key_from_section(username, "salt", None):
            salt = uuid.uuid4().hex
            SummitRCMConfigManage.update_key_from_section(username, "salt", salt)
            SummitRCMConfigManage.update_key_from_section(
                username,
                "password",
                hashlib.sha256(salt.encode() + password.encode()).hexdigest(),
            )
            return SummitRCMConfigManage.save()
        return False

    @staticmethod
    def get_permission(username: str) -> str:
        """Retrieve the permissions for the user with the specified username"""

        return SummitRCMConfigManage.get_key_from_section(username, "permission", None)

    @staticmethod
    def update_permission(username: str, permission: str) -> bool:
        """Update the permissions for the user with the specified username and permssions"""

        if permission and SummitRCMConfigManage.get_key_from_section(
            username, "permission", None
        ):
            return SummitRCMConfigManage.update_key_from_section(
                username, "permission", permission
            )
        return False

    @staticmethod
    def get_number_of_users() -> int:
        """Retrieve the current numer of users (including root)"""
        return SummitRCMConfigManage.get_section_size_by_key("password")

    @staticmethod
    def get_users_dict() -> dict:
        """
        Retrieve a dictionary of all users and their configuration (excluding the default user)
        """

        user_dict = SummitRCMConfigManage.get_sections_and_key("permission")
        if user_dict:
            # Default user shouldn't be listed as its permission can't be updated by Summit RCM
            default_username = (
                ServerConfig()
                .get_parser()
                .get("summit-rcm", "default_username", fallback="root")
                .strip('"')
            )
            user_dict.pop(default_username, None)
        return user_dict

    @staticmethod
    def update_user(username: str, password: str, permission: str) -> bool:
        """
        Update the password and permissions for the user with the specified username, new password,
        and new permissions
        """

        return UserService.update_password(
            username, password
        ) and UserService.update_permission(username, permission)

    @staticmethod
    def max_users_reached() -> bool:
        """Retrieve whether or not the max allowed number of users has been reached"""
        return (
            UserService.get_number_of_users()
            >= SystemSettingsManage.get_max_web_clients()
        )
