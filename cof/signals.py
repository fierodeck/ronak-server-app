from django.db.models.signals import pre_save, m2m_changed
from django.dispatch import receiver
from .models import Cof


@receiver(pre_save, sender=Cof)
def cof_pre_save(sender, instance, **kwargs):
    # Auto-calculate total price before saving
    if instance.price_single and instance.quantity:
        try:
            instance.price_total = str(round(float(instance.price_single) * int(instance.quantity), 2))
        except ValueError:
            pass


@receiver(m2m_changed, sender=Cof.similar_cofs.through)
def cof_m2m_changed(sender, instance, action, **kwargs):
    # If X is similar to Y and Z, then Y, Z and any newly connected Cof become mutually similar
    if action == 'post_add':
        group = set(instance.similar_cofs.all()) | {instance}

        # Expand to all transitively connected cofs
        has_new = True
        while has_new:
            has_new = False
            for c in list(group):
                for related in c.similar_cofs.all():
                    if related not in group:
                        group.add(related)
                        has_new = True

        # Link all members in the group to each other
        for cof in list(group):
            missing = group - {cof} - set(cof.similar_cofs.all())
            if missing:
                cof.similar_cofs.add(*missing)
