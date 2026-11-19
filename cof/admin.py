from django.contrib import admin, messages
from django.db import models
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Cof


class AvailabilityFilter(admin.SimpleListFilter):
    title = 'Stock Availability'
    parameter_name = 'availability'

    def lookups(self, request, model_admin):
        return [
            ('available', 'Available (Qty >= 1)'),
            ('not_available', 'Not Available (Qty = 0)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'available':
            return queryset.filter(quantity__gte=1)
        if self.value() == 'not_available':
            return queryset.filter(models.Q(quantity__lte=0) | models.Q(quantity__isnull=True))
        return queryset


class HasSimilarCofsFilter(admin.SimpleListFilter):
    title = 'Similar Cofs Status'
    parameter_name = 'has_similar'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'Has Similar Cofs'),
            ('no', 'No Similar Cofs'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(similar_cofs__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(similar_cofs__isnull=True)
        return queryset


@admin.register(Cof)
class CofAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'quantity',
        'price_single',
        'price_total',
        'is_available',
        'similar_cofs_names',
    )
    search_fields = ('name', 'notes')
    list_filter = (
        AvailabilityFilter,
        HasSimilarCofsFilter,
        'created_at',
        'updated_at',
    )
    filter_horizontal = ('similar_cofs',)
    readonly_fields = ('price_total', 'identical_cofs_list')

    fields = (
        'name',
        'quantity',
        'price_single',
        'price_total',
        'image',
        'similar_cofs',
        'identical_cofs_list',
        'notes',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('similar_cofs')

    @admin.display(boolean=True, description='Available', ordering='quantity')
    def is_available(self, obj):
        return bool(obj.quantity and obj.quantity >= 1)

    @admin.display(description='Similar Cofs')
    def similar_cofs_names(self, obj):
        names = [c.name for c in obj.similar_cofs.all()]
        return ", ".join(names) if names else "-"

    def identical_cofs_list(self, obj):
        if not obj.pk or not obj.similar_cofs.exists():
            return "No identical Cofs added yet."

        items = []
        for c in obj.similar_cofs.all():
            url = reverse('admin:cof_cof_change', args=[c.id])
            if not c.quantity or c.quantity <= 0:
                status = ' <span style="color: red; font-weight: bold;">(Not Available)</span>'
            else:
                status = f' (Qty: {c.quantity})'

            items.append(f'<li><a href="{url}">#{c.id} - {c.name}</a>{status}</li>')

        return mark_safe(f"<ul style='margin:0; padding-left:18px;'>{''.join(items)}</ul>")

    identical_cofs_list.short_description = "Similar Cofs"

    def save_model(self, request, obj, form, change):
        if not change:
            # If a Cof with the same name already exists, just increase quantity
            existing = Cof.objects.filter(name__iexact=obj.name.strip()).first()
            if existing:
                added_qty = obj.quantity or 1
                existing.quantity = (existing.quantity or 0) + added_qty
                if obj.price_single:
                    existing.price_single = obj.price_single
                existing.save()

                # Add any selected similar_cofs
                similars = form.cleaned_data.get('similar_cofs')
                if similars:
                    existing.similar_cofs.add(*similars)

                messages.success(
                    request,
                    f"Cof '{existing.name}' already existed. Quantity increased by +{added_qty}. Total: {existing.quantity}."
                )
                obj.pk = existing.pk
                request._merged = existing
                return

        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        if hasattr(request, '_merged'):
            existing = request._merged
            return HttpResponseRedirect(reverse('admin:cof_cof_change', args=[existing.pk]))
        return super().response_add(request, obj, post_url_continue)
