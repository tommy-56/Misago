from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.dispatch import Signal, receiver
from django.utils import timezone
from django.utils.translation import ugettext as _

from misago.conf import settings
from misago.core.pgutils import chunk_queryset

from .models import AuditTrail
from .profilefields import profilefields


UserModel = get_user_model()

anonymize_user_content = Signal()
archive_user_data = Signal()
delete_user_content = Signal()
remove_old_ips = Signal()
username_changed = Signal()


@receiver(archive_user_data)
def archive_user_details(sender, data_archiver=None, **kwargs):
    data_archiver.write_data_file('details', {
        _('Username'): sender.username,
        _('E-mail'): sender.email,
        _('Joined on'): sender.joined_on,
        _('Joined from ip'): sender.joined_from_ip or 'unavailable',
    })


@receiver(archive_user_data)
def archive_user_profile_fields(sender, data_archiver=None, **kwargs):
    clean_profile_fields = {}
    for profile_fields_group in profilefields.get_fields_groups():
        for profile_field in profile_fields_group['fields']:
            if sender.profile_fields.get(profile_field.fieldname):
                field_value = sender.profile_fields[profile_field.fieldname]
                clean_profile_fields[str(profile_field.label)] = field_value
                
    if clean_profile_fields:
        data_archiver.write_data_file('profile_fields', clean_profile_fields)


@receiver(archive_user_data)
def archive_user_avatar(sender, data_archiver=None, **kwargs):
    collection = data_archiver.create_collection('avatar')
    collection.write_model_file(sender.avatar_tmp)
    collection.write_model_file(sender.avatar_src)
    for avatar in sender.avatar_set.iterator():
        collection.write_model_file(avatar.image)


@receiver(archive_user_data)
def archive_user_audit_trail(sender, data_archiver=None, **kwargs):
    collection = data_archiver.create_collection('audit_trail')
    queryset = sender.audittrail_set.order_by('id')
    for audit_trail in chunk_queryset(queryset):
        collection.write_data_file(audit_trail.created_at, audit_trail.ip_address)


@receiver(archive_user_data)
def archive_user_name_history(sender, data_archiver=None, **kwargs):
    collection = data_archiver.create_collection('name_history')
    for name_change in sender.namechanges.order_by('id').iterator():
        collection.write_data_file(name_change.changed_on, {
            _("New username"): name_change.new_username,
            _("Old username"): name_change.old_username,
        })


@receiver(username_changed)
def handle_name_change(sender, **kwargs):
    sender.user_renames.update(changed_by_username=sender.username)


@receiver(remove_old_ips)
def remove_old_registrations_ips(sender, **kwargs):
    datetime_cutoff = timezone.now() - timedelta(days=settings.MISAGO_IP_STORE_TIME)
    ip_is_too_new = Q(joined_on__gt=datetime_cutoff)
    ip_is_already_removed = Q(joined_from_ip__isnull=True)
    
    queryset = UserModel.objects.exclude(ip_is_too_new | ip_is_already_removed)
    queryset.update(joined_from_ip=None)


@receiver(remove_old_ips)
def remove_old_audit_trails(sender, **kwargs):
    removal_cutoff = timezone.now() - timedelta(days=settings.MISAGO_IP_STORE_TIME)
    AuditTrail.objects.filter(created_at__lte=removal_cutoff).delete()
