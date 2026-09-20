"""Tests covering stock arithmetic, access control and the main user flows."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import BloodBagInfo, BloodBankInfo, UserProfile


def make_branch(zone='North', **stock):
    defaults = {
        'address': f'{zone} branch, Dhaka',
        'phone': '+8801712345678',
        'email': f'{zone.lower()}@bloodbank.org',
    }
    return BloodBankInfo.objects.create(branch_zone=zone, **defaults, **stock)


def make_member(email='member@example.com', password='Str0ng-Passphrase!', **profile):
    user = User.objects.create_user(
        username=email, email=email, password=password,
        first_name='Test', last_name='Member',
    )
    defaults = {
        'gender': 'Male', 'phone_number': '+8801712345678', 'address': 'Dhaka',
        'age': 25, 'zone': 'North', 'blood': 'O+',
    }
    UserProfile.objects.create(user=user, **{**defaults, **profile})
    return user


def make_manager(zone='North', email='manager@example.com', password='Str0ng-Passphrase!'):
    user = User.objects.create_superuser(username=email, email=email, password=password)
    UserProfile.objects.create(
        user=user, gender='Female', phone_number='+8801712345678', address='Dhaka',
        age=40, zone=zone, blood='A+', working_zone=zone,
    )
    return user


class BloodBankStockTests(TestCase):
    def test_field_for_maps_every_blood_group(self):
        self.assertEqual(BloodBankInfo.field_for('AB-'), 'ab_negative')
        with self.assertRaises(ValueError):
            BloodBankInfo.field_for('C+')

    def test_adjust_stock_adds_and_removes_bags(self):
        branch = make_branch(o_positive=5)
        self.assertEqual(branch.adjust_stock('O+', 3), 8)
        self.assertEqual(branch.adjust_stock('O+', -2), 6)
        branch.refresh_from_db()
        self.assertEqual(branch.o_positive, 6)

    def test_adjust_stock_refuses_to_go_negative(self):
        branch = make_branch(o_positive=1)
        with self.assertRaises(ValueError):
            branch.adjust_stock('O+', -2)
        branch.refresh_from_db()
        self.assertEqual(branch.o_positive, 1)


class AccessControlTests(TestCase):
    def test_manager_pages_reject_anonymous_visitors(self):
        for name in ('dashboard', 'blood_details', 'blood_entry', 'blood_issue', 'user_list'):
            with self.subTest(view=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response['Location'])

    def test_manager_pages_reject_ordinary_members(self):
        make_member()
        self.client.login(username='member@example.com', password='Str0ng-Passphrase!')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('home'))

    def test_search_requires_login(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 302)


class RegistrationTests(TestCase):
    payload = {
        'fname': 'Ayesha', 'lname': 'Rahman', 'email': 'ayesha@example.com',
        'password': 'Str0ng-Passphrase!', 'phone': '+8801712345678', 'age': '24',
        'address': 'Mirpur, Dhaka', 'zone': 'North', 'blood': 'B+', 'gender': 'Female',
    }

    def test_successful_registration_creates_a_profile(self):
        response = self.client.post(reverse('register'), self.payload)
        self.assertRedirects(response, reverse('home'))
        user = User.objects.get(username='ayesha@example.com')
        self.assertEqual(user.profile.blood, 'B+')

    def test_new_members_do_not_get_admin_access(self):
        self.client.post(reverse('register'), self.payload)
        user = User.objects.get(username='ayesha@example.com')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_underage_applicants_are_rejected(self):
        response = self.client.post(reverse('register'), {**self.payload, 'age': '15'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='ayesha@example.com').exists())

    def test_duplicate_email_is_rejected(self):
        make_member(email='ayesha@example.com')
        response = self.client.post(reverse('register'), self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='ayesha@example.com').count(), 1)


class StockMovementTests(TestCase):
    def setUp(self):
        make_manager()
        self.client.login(username='manager@example.com', password='Str0ng-Passphrase!')

    def test_entry_increases_stock_and_writes_a_ledger_row(self):
        branch = make_branch(o_positive=2)
        response = self.client.post(reverse('blood_entry'), {
            'date': '2026-01-15', 'blood_type': 'O+', 'quantity': '4',
        })
        self.assertRedirects(response, reverse('blood_details'))
        branch.refresh_from_db()
        self.assertEqual(branch.o_positive, 6)
        record = BloodBagInfo.objects.get()
        self.assertEqual(record.quantity, 4)
        self.assertEqual(record.branch, 'North')

    def test_issue_decreases_stock_and_records_a_negative_quantity(self):
        branch = make_branch(a_positive=10)
        self.client.post(reverse('blood_issue'), {
            'date': '2026-01-15', 'blood_type': 'A+', 'quantity': '3',
        })
        branch.refresh_from_db()
        self.assertEqual(branch.a_positive, 7)
        self.assertEqual(BloodBagInfo.objects.get().quantity, -3)

    def test_issuing_more_than_available_changes_nothing(self):
        branch = make_branch(a_positive=1)
        response = self.client.post(reverse('blood_issue'), {
            'date': '2026-01-15', 'blood_type': 'A+', 'quantity': '5',
        })
        self.assertEqual(response.status_code, 200)
        branch.refresh_from_db()
        self.assertEqual(branch.a_positive, 1)
        self.assertFalse(BloodBagInfo.objects.exists())

    def test_missing_branch_record_does_not_crash(self):
        response = self.client.post(reverse('blood_entry'), {
            'date': '2026-01-15', 'blood_type': 'A+', 'quantity': '1',
        })
        self.assertEqual(response.status_code, 200)


class SearchTests(TestCase):
    def setUp(self):
        self.user = make_member()
        self.client.login(username='member@example.com', password='Str0ng-Passphrase!')

    def test_search_reports_availability_against_branch_stock(self):
        make_branch(o_positive=4)
        response = self.client.post(reverse('search'), {
            'zone': 'North', 'blood_group': 'O+', 'quantity': '3',
        })
        self.assertTrue(response.context['availability'])
        self.assertEqual(response.context['in_stock'], 4)

    def test_search_without_a_branch_record_reports_unavailable(self):
        response = self.client.post(reverse('search'), {
            'zone': 'South', 'blood_group': 'O+', 'quantity': '1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['availability'])

    def test_only_opted_in_donors_are_listed(self):
        make_branch(o_positive=1)
        volunteer = make_member(email='donor@example.com', is_donor=True)
        response = self.client.post(reverse('search'), {
            'zone': 'North', 'blood_group': 'O+', 'quantity': '1',
        })
        listed = [profile.user_id for profile in response.context['donors']]
        self.assertIn(volunteer.id, listed)
        self.assertNotIn(self.user.id, listed)


class MemberRosterTests(TestCase):
    def test_deactivate_requires_post_and_removes_the_member(self):
        make_manager()
        member = make_member()
        self.client.login(username='manager@example.com', password='Str0ng-Passphrase!')
        url = reverse('deactivate_user', args=[member.id])

        self.assertEqual(self.client.get(url).status_code, 405)

        response = self.client.post(url)
        self.assertRedirects(response, reverse('user_list'))
        member.refresh_from_db()
        self.assertFalse(member.is_active)

    def test_toggle_donor_status_only_affects_the_signed_in_member(self):
        member = make_member()
        other = make_member(email='other@example.com')
        self.client.login(username='member@example.com', password='Str0ng-Passphrase!')

        self.client.post(reverse('toggle_donor_status'))
        member.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(member.profile.is_donor)
        self.assertFalse(other.profile.is_donor)
