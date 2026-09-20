"""Database models for the Blood Donation Camp application.

Three entities carry the whole domain:

* ``UserProfile``   - the donation-related details attached to a Django user.
* ``BloodBankInfo`` - the current stock of a branch, one row per zone.
* ``BloodBagInfo``  - an append-only ledger of every stock movement.
"""

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

# --------------------------------------------------------------------------- #
# Shared choices
# --------------------------------------------------------------------------- #

BLOOD_GROUP_CHOICES = [
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
]

ZONE_CHOICES = [
    ('North', 'Dhaka North'),
    ('South', 'Dhaka South'),
]

GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
]

#: Maps a human blood group to the ``BloodBankInfo`` column that stores it.
#: Keeping the mapping in one place removes the long if/elif chains that used
#: to be duplicated across the views.
BLOOD_GROUP_FIELDS = {
    'A+': 'a_positive',
    'A-': 'a_negative',
    'B+': 'b_positive',
    'B-': 'b_negative',
    'O+': 'o_positive',
    'O-': 'o_negative',
    'AB+': 'ab_positive',
    'AB-': 'ab_negative',
}

phone_validator = RegexValidator(
    regex=r'^\+?[0-9][0-9\s\-]{5,19}$',
    message='Enter a valid contact number (digits, spaces and dashes only).',
)


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #

class UserProfile(models.Model):
    """Donation-related details for a registered user.

    Branch managers are the users flagged as ``is_superuser``; for them
    ``working_zone`` records the branch they operate and ``zone`` is unused.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    address = models.CharField(max_length=255)
    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(65)],
        help_text='Donors must be between 18 and 65 years old.',
    )
    zone = models.CharField(max_length=5, choices=ZONE_CHOICES)
    blood = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    is_donor = models.BooleanField(
        default=False,
        help_text='Opted in to be contacted as a volunteer donor.',
    )
    working_zone = models.CharField(
        max_length=5,
        choices=ZONE_CHOICES,
        blank=True,
        null=True,
        help_text='Branch managed by this user. Managers only.',
    )

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        verbose_name = 'user profile'
        verbose_name_plural = 'user profiles'

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username


class BloodBankInfo(models.Model):
    """Current stock and contact details for a single branch."""

    branch_zone = models.CharField(max_length=5, choices=ZONE_CHOICES, unique=True)
    a_positive = models.PositiveIntegerField(default=0)
    a_negative = models.PositiveIntegerField(default=0)
    b_positive = models.PositiveIntegerField(default=0)
    b_negative = models.PositiveIntegerField(default=0)
    o_positive = models.PositiveIntegerField(default=0)
    o_negative = models.PositiveIntegerField(default=0)
    ab_positive = models.PositiveIntegerField(default=0)
    ab_negative = models.PositiveIntegerField(default=0)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField()

    class Meta:
        ordering = ['branch_zone']
        verbose_name = 'blood bank branch'
        verbose_name_plural = 'blood bank branches'

    def __str__(self):
        return f'{self.get_branch_zone_display()} branch'

    @staticmethod
    def field_for(blood_group):
        """Return the stock column name for ``blood_group``.

        Raises ``ValueError`` for an unknown group so a bad form value fails
        loudly instead of silently updating nothing.
        """
        try:
            return BLOOD_GROUP_FIELDS[blood_group]
        except KeyError:
            raise ValueError(f'Unknown blood group: {blood_group!r}') from None

    def stock_for(self, blood_group):
        """Number of bags of ``blood_group`` currently held by this branch."""
        return getattr(self, self.field_for(blood_group))

    def adjust_stock(self, blood_group, delta):
        """Add ``delta`` bags (negative to issue) and save.

        Returns the new stock level. Raises ``ValueError`` when the branch does
        not hold enough bags, which keeps the column from going negative.
        """
        field = self.field_for(blood_group)
        new_value = getattr(self, field) + delta
        if new_value < 0:
            raise ValueError(
                f'Only {getattr(self, field)} bag(s) of {blood_group} '
                f'available at the {self.get_branch_zone_display()} branch.'
            )
        setattr(self, field, new_value)
        self.save(update_fields=[field])
        return new_value

    @property
    def total_bags(self):
        return sum(getattr(self, field) for field in BLOOD_GROUP_FIELDS.values())


class BloodBagInfo(models.Model):
    """One stock movement.

    ``quantity`` is signed: positive rows are bags collected into the branch,
    negative rows are bags issued out of it. The table is therefore an
    append-only ledger that explains how a ``BloodBankInfo`` row reached its
    current value.
    """

    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    date = models.DateField()
    branch = models.CharField(max_length=5, choices=ZONE_CHOICES, default='North')
    quantity = models.IntegerField(
        default=0,
        help_text='Positive when blood is collected, negative when it is issued.',
    )
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blood_bag_entries',
    )

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'blood bag record'
        verbose_name_plural = 'blood bag records'
        indexes = [models.Index(fields=['branch', 'blood_group'])]

    def __str__(self):
        action = 'collected' if self.quantity >= 0 else 'issued'
        return f'{abs(self.quantity)} x {self.blood_group} {action} ({self.date})'
