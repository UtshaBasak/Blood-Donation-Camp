from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=7, choices=[('Male','Male'),('Female','Female')])
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    age = models.CharField(max_length=3)
    zone = models.CharField(max_length=8, choices=[('North','North'),('South','South')])
    is_donor = models.BooleanField(default=False)
    blood = models.CharField(max_length=3, choices=[
                ('A+', 'A+'),
                ('A-', 'A-'),
                ('B+', 'B+'),
                ('B-', 'B-'),
                ('AB+', 'AB+'),
                ('AB-', 'AB-'),
                ('O+', 'O+'),
                ('O-', 'O-'),
            ])
    working_zone = models.CharField(max_length=255, null=True)


    def __str__(self):
        return self.user.username


class BloodBagInfo(models.Model):
    id = models.AutoField(primary_key=True)
    blood_group = models.CharField(max_length=3)
    date = models.DateField()
    branch = models.CharField(default='North', max_length=20)
    quantity = models.IntegerField(default=0)
    # is_active = models.BooleanField(default=True)


class BloodBankInfo(models.Model):
    branch_zone = models.CharField(max_length=5, choices=(('North', 'North'), ('South', 'South')))
    blood_type_choices = (
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-'),
    )
    a_positive = models.PositiveIntegerField(default=0)
    a_negative = models.PositiveIntegerField(default=0)
    b_positive = models.PositiveIntegerField(default=0)
    b_negative = models.PositiveIntegerField(default=0)
    o_positive = models.PositiveIntegerField(default=0)
    o_negative = models.PositiveIntegerField(default=0)
    ab_positive = models.PositiveIntegerField(default=0)
    ab_negative = models.PositiveIntegerField(default=0)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
