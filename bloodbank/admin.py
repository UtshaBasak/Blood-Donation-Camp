"""Django admin registrations for the bloodbank models."""

from django.contrib import admin

from .models import BloodBagInfo, BloodBankInfo, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'blood', 'zone', 'phone_number', 'is_donor')
    list_filter = ('blood', 'zone', 'is_donor', 'gender')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone_number')
    list_select_related = ('user',)
    autocomplete_fields = ('user',)

    @admin.display(description='Email', ordering='user__email')
    def email(self, obj):
        return obj.user.email


@admin.register(BloodBankInfo)
class BloodBankInfoAdmin(admin.ModelAdmin):
    list_display = (
        'branch_zone', 'a_positive', 'a_negative', 'b_positive', 'b_negative',
        'o_positive', 'o_negative', 'ab_positive', 'ab_negative', 'total_bags',
    )
    search_fields = ('branch_zone', 'address', 'email')
    fieldsets = (
        ('Branch', {'fields': ('branch_zone', 'address', 'phone', 'email')}),
        ('Stock (bags)', {
            'fields': (
                ('a_positive', 'a_negative'),
                ('b_positive', 'b_negative'),
                ('o_positive', 'o_negative'),
                ('ab_positive', 'ab_negative'),
            )
        }),
    )

    @admin.display(description='Total bags')
    def total_bags(self, obj):
        return obj.total_bags


@admin.register(BloodBagInfo)
class BloodBagInfoAdmin(admin.ModelAdmin):
    list_display = ('date', 'branch', 'blood_group', 'quantity', 'recorded_by')
    list_filter = ('branch', 'blood_group', 'date')
    search_fields = ('blood_group', 'branch')
    date_hierarchy = 'date'
    list_select_related = ('recorded_by',)
