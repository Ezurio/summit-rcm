"""Module to hold SpecTree Tags"""

from spectree import Tag


login_tag = Tag(
    name="Login",
    description="Endpoints related to session cookies, logins, and users",
)


system_tag = Tag(
    name="System",
    description="Endpoints related to general system configuration and control",
)


network_tag = Tag(
    name="Network",
    description="Endpoints related to networking configuration and control",
)
