"""Request handlers for the Blood Donation Camp application.

Two audiences share the same URL space:

* Members register, manage their profile and search for available blood.
* Branch managers (Django superusers) record stock movements and administer
  the member list from the dashboard.

Every view that reads or writes member data is behind ``@login_required``, and
every manager-only view is behind ``@manager_required``.
"""

from functools import wraps

from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import (
    BLOOD_GROUP_CHOICES,
    GENDER_CHOICES,
    ZONE_CHOICES,
    BloodBagInfo,
    BloodBankInfo,
    UserProfile,
)

BLOOD_GROUPS = [value for value, _ in BLOOD_GROUP_CHOICES]
ZONES = [value for value, _ in ZONE_CHOICES]
GENDERS = [value for value, _ in GENDER_CHOICES]

#: Choice lists every form template needs, so the options live in one place
#: instead of being hand-written into each <select>.
FORM_CONTEXT = {
    'blood_groups': BLOOD_GROUP_CHOICES,
    'zones': ZONE_CHOICES,
    'genders': GENDER_CHOICES,
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def manager_required(view):
    """Allow only signed-in branch managers (superusers) through."""

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'You do not have access to that page.')
            return redirect('home')
        return view(request, *args, **kwargs)

    return wrapper


def get_profile(user):
    """Return the user's profile, or ``None`` if they never completed one.

    Superusers created with ``createsuperuser`` have no profile, so callers
    must handle the ``None`` case rather than assume one exists.
    """
    return UserProfile.objects.filter(user=user).select_related('user').first()


def parse_quantity(raw):
    """Parse a bag count from form input, or ``None`` when it is not valid."""
    try:
        quantity = int(raw)
    except (TypeError, ValueError):
        return None
    return quantity if quantity > 0 else None


# --------------------------------------------------------------------------- #
# Public pages
# --------------------------------------------------------------------------- #

def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html', {'branches': BloodBankInfo.objects.all()})


# --------------------------------------------------------------------------- #
# Authentication
# --------------------------------------------------------------------------- #

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = auth.authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html', {'username': username})
        auth.login(request, user)
        messages.success(request, 'Welcome back!')
        return redirect('home')

    return render(request, 'login.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method != 'POST':
        return render(request, 'register.html', FORM_CONTEXT)

    fields = ('fname', 'lname', 'email', 'phone', 'age', 'address', 'zone', 'blood', 'gender')
    data = {key: request.POST.get(key, '').strip() for key in fields}
    password = request.POST.get('password', '')
    context = {**FORM_CONTEXT, 'form_data': data}

    errors = []
    if not all(data.values()) or not password:
        errors.append('All fields are required.')
    if data['email'] and User.objects.filter(username__iexact=data['email']).exists():
        errors.append('That email address is already registered.')
    if data['zone'] and data['zone'] not in ZONES:
        errors.append('Select a valid zone.')
    if data['blood'] and data['blood'] not in BLOOD_GROUPS:
        errors.append('Select a valid blood group.')
    if data['gender'] and data['gender'] not in GENDERS:
        errors.append('Select a valid gender.')

    age = None
    if data['age']:
        try:
            age = int(data['age'])
        except ValueError:
            errors.append('Age must be a number.')
        else:
            if not 18 <= age <= 65:
                errors.append('Donors must be between 18 and 65 years old.')

    if password:
        try:
            validate_password(password)
        except ValidationError as exc:
            errors.extend(exc.messages)

    if errors:
        for error in errors:
            messages.error(request, error)
        return render(request, 'register.html', context)

    with transaction.atomic():
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=password,
            first_name=data['fname'],
            last_name=data['lname'],
        )
        UserProfile.objects.create(
            user=user,
            phone_number=data['phone'],
            age=age,
            address=data['address'],
            gender=data['gender'],
            zone=data['zone'],
            blood=data['blood'],
        )

    user = auth.authenticate(request, username=data['email'], password=password)
    if user is not None:
        auth.login(request, user)
    messages.success(request, 'Your account has been created.')
    return redirect('home')


@require_POST
def logout_view(request):
    auth.logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('home')


# --------------------------------------------------------------------------- #
# Member area
# --------------------------------------------------------------------------- #

@login_required
def profile(request):
    return render(request, 'user_profile.html', {'profile': get_profile(request.user)})


@login_required
@require_POST
def toggle_donor_status(request):
    """Opt the signed-in member in or out of the volunteer donor list."""
    user_profile = get_profile(request.user)
    if user_profile is None:
        messages.error(request, 'Complete your profile before opting in as a donor.')
        return redirect('profile')

    user_profile.is_donor = not user_profile.is_donor
    user_profile.save(update_fields=['is_donor'])
    messages.success(
        request,
        'You are now listed as a volunteer donor.' if user_profile.is_donor
        else 'You have been removed from the volunteer donor list.',
    )
    return redirect('profile')


@login_required
def search(request):
    """Check branch stock for a blood group and list volunteer donors nearby."""
    context = {**FORM_CONTEXT, 'searched': False}

    if request.method != 'POST':
        return render(request, 'search.html', context)

    zone = request.POST.get('zone', '')
    blood_group = request.POST.get('blood_group', '')
    quantity = parse_quantity(request.POST.get('quantity'))

    if zone not in ZONES or blood_group not in BLOOD_GROUPS:
        messages.error(request, 'Select a valid zone and blood group.')
        return render(request, 'search.html', context)
    if quantity is None:
        messages.error(request, 'Enter how many bags you need (1 or more).')
        return render(request, 'search.html', context)

    branch = BloodBankInfo.objects.filter(branch_zone=zone).first()
    if branch is None:
        messages.warning(request, 'No blood bank is registered for that zone yet.')
    in_stock = branch.stock_for(blood_group) if branch else 0

    context.update({
        'searched': True,
        'availability': quantity <= in_stock,
        'in_stock': in_stock,
        'requested': quantity,
        'selected_zone': zone,
        'selected_blood_group': blood_group,
        'donors': UserProfile.objects.filter(
            zone=zone, blood=blood_group, is_donor=True, user__is_active=True
        ).select_related('user'),
    })
    return render(request, 'search.html', context)


# --------------------------------------------------------------------------- #
# Manager area
# --------------------------------------------------------------------------- #

@manager_required
def dashboard(request):
    return render(request, 'dashboard.html', {
        'branches': BloodBankInfo.objects.all(),
        'member_count': User.objects.filter(is_active=True, is_superuser=False).count(),
    })


@manager_required
def blood_details(request):
    return render(request, 'blood_details.html', {
        'blood_info': BloodBankInfo.objects.all(),
        'recent_records': BloodBagInfo.objects.select_related('recorded_by')[:20],
    })


@manager_required
def user_list(request):
    members = (
        UserProfile.objects
        .filter(user__is_active=True, user__is_superuser=False)
        .select_related('user')
    )
    return render(request, 'user_list.html', {'users': members})


@manager_required
@require_POST
def deactivate_user(request, user_id):
    """Remove a member from the active roster.

    The account is deactivated rather than deleted so that the blood bag ledger
    keeps pointing at a real user record.
    """
    member = get_object_or_404(User, id=user_id, is_superuser=False)
    member.is_active = False
    member.save(update_fields=['is_active'])
    messages.success(request, 'The member has been removed from the roster.')
    return redirect('user_list')


def _record_movement(request, template, *, sign, success_message):
    """Shared handler for collecting (``sign=1``) and issuing (``sign=-1``) blood."""
    manager_profile = get_profile(request.user)
    zone = manager_profile.working_zone if manager_profile else None
    context = {**FORM_CONTEXT, 'working_zone': zone}

    if not zone:
        messages.error(
            request,
            'Your account has no working zone assigned. Set one in the Django '
            'admin before recording stock movements.',
        )
        return render(request, template, context)

    if request.method != 'POST':
        return render(request, template, context)

    date = request.POST.get('date', '')
    blood_group = request.POST.get('blood_type', '')
    quantity = parse_quantity(request.POST.get('quantity'))

    if not date or blood_group not in BLOOD_GROUPS:
        messages.error(request, 'Select a valid date and blood group.')
        return render(request, template, context)
    if quantity is None:
        messages.error(request, 'Quantity must be 1 or more.')
        return render(request, template, context)

    try:
        with transaction.atomic():
            branch = BloodBankInfo.objects.select_for_update().get(branch_zone=zone)
            branch.adjust_stock(blood_group, sign * quantity)
            BloodBagInfo.objects.create(
                blood_group=blood_group,
                date=date,
                quantity=sign * quantity,
                branch=zone,
                recorded_by=request.user,
            )
    except BloodBankInfo.DoesNotExist:
        messages.error(request, 'No blood bank record exists for your working zone.')
        return render(request, template, context)
    except ValueError as exc:
        messages.error(request, str(exc))
        return render(request, template, context)

    messages.success(request, success_message.format(quantity=quantity, blood_group=blood_group))
    return redirect('blood_details')


@manager_required
def blood_entry(request):
    """Record bags collected into the manager's branch."""
    return _record_movement(
        request,
        'blood_entry.html',
        sign=1,
        success_message='Added {quantity} bag(s) of {blood_group} to stock.',
    )


@manager_required
def blood_issue(request):
    """Record bags issued out of the manager's branch."""
    return _record_movement(
        request,
        'blood_issue.html',
        sign=-1,
        success_message='Issued {quantity} bag(s) of {blood_group}.',
    )
