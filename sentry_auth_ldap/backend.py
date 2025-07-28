from django_auth_ldap.backend import LDAPBackend
from django.conf import settings

from packaging import version
from sentry import __version__ as sentry_version

def compare_versions(current: str, required: str) -> bool:
    """
    Check if the current version meets the required version.

    :param current: The current version string
    :param required: The required version string
    :return: True if the current version is greater than or equal to the required version, otherwise False
    """
    return version.parse(current) >= version.parse(required)

from sentry.models import Organization, OrganizationMember, OrganizationMemberTeam, Team, UserOption

# Import different models for backwards compatibility
if compare_versions(sentry_version, "24.10.0"):
    from sentry.users.models import UserEmail
elif compare_versions(sentry_version, "24.8.0"):
    from sentry.users.models.useremail import UserEmail
else:
    from sentry.models import UserEmail

def _get_effective_sentry_role(ldap_user):
    role_priority_order = [
        'member',
        'admin',
        'manager',
        'owner',
    ]

    role_mapping = getattr(settings, 'AUTH_LDAP_SENTRY_GROUP_ROLE_MAPPING', None)
    if not role_mapping:
        return None

    group_names = ldap_user.group_names
    if not group_names:
        return None

    applicable_roles = [role for role, groups in role_mapping.items() if group_names.intersection(groups)]
    if not applicable_roles:
        return None

    highest_role = [role for role in role_priority_order if role in applicable_roles][-1]
    return highest_role


def _get_effective_sentry_teams(ldap_user):
    team_mapping = getattr(settings, 'AUTH_LDAP_SENTRY_TEAM_MAPPING', None)
    if not team_mapping:
        return []

    group_names = ldap_user.group_names
    if not group_names:
        return []

    return [team for team, groups in team_mapping.items() if group_names.intersection(groups)]


def _find_default_organization():
    organization_slug = getattr(settings, 'AUTH_LDAP_SENTRY_DEFAULT_ORGANIZATION', None)
    if organization_slug:
        return Organization.objects.filter(slug=organization_slug).first()

    # For backward compatibility
    organization_name = getattr(settings, 'AUTH_LDAP_DEFAULT_SENTRY_ORGANIZATION', None)
    if organization_name:
        return Organization.objects.filter(name=organization_name).first()

    return None


class SentryLdapBackend(LDAPBackend):
    def get_or_build_user(self, username, ldap_user):
        (user, built) = super().get_or_build_user(username, ldap_user)

        user.is_managed = True

        # Add the user email address
        mail_attr_name = self.settings.USER_ATTR_MAP.get('email', 'mail')
        mail_attr = ldap_user.attrs.get(mail_attr_name)
        if mail_attr:
            email = mail_attr[0]
        elif hasattr(settings, 'AUTH_LDAP_DEFAULT_EMAIL_DOMAIN'):
            email = username + '@' + settings.AUTH_LDAP_DEFAULT_EMAIL_DOMAIN
        else:
            email = None

        if email:
            user.email = email

        user.save()

        if mail_attr and getattr(settings, 'AUTH_LDAP_MAIL_VERIFIED', False):
            defaults = { 'is_verified': True }
        else:
            defaults = None

        for mail in mail_attr or [email]:
            UserEmail.objects.update_or_create(defaults=defaults, user=user, email=mail)

        organization = _find_default_organization()
        if organization:
            sentry_role_from_ldap_group = _get_effective_sentry_role(ldap_user)
            try:
                organization_member = OrganizationMember.objects.get(organization=organization, user_id=user.id)
                if sentry_role_from_ldap_group:
                    # The role mapped from LDAP will always overrides any manual changes the user might have made
                    organization_member.role = sentry_role_from_ldap_group
                    organization_member.save()
            except OrganizationMember.DoesNotExist:
                # Assign the user to the organization if not exists
                organization_member = OrganizationMember.objects.create(
                    organization=organization,
                    user_id=user.id,
                    role=sentry_role_from_ldap_group or getattr(settings, 'AUTH_LDAP_SENTRY_ORGANIZATION_ROLE_TYPE', None),
                    has_global_access=getattr(settings, 'AUTH_LDAP_SENTRY_ORGANIZATION_GLOBAL_ACCESS', False),
                    flags=getattr(OrganizationMember.flags, 'sso:linked'),
                )
            sentry_teams_from_ldap_group = _get_effective_sentry_teams(ldap_user)
            for team_slug in sentry_teams_from_ldap_group:
                try:
                    team = Team.objects.get(organization=organization, slug=team_slug)
                    OrganizationMemberTeam.objects.create_or_update(team=team, organizationmember=organization_member)
                except Team.DoesNotExist:
                    pass

        # Set subscribe_by_default for new user
        if built and not getattr(settings, 'AUTH_LDAP_SENTRY_SUBSCRIBE_BY_DEFAULT', True):
            UserOption.objects.set_value(
                user=user,
                project=None,
                key='subscribe_by_default',
                value='0',
            )

        return (user, built)
