from django.contrib.auth import user_logged_in
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib import messages
from .models import UserProfile, BloodBagInfo, BloodBankInfo


# Create your views here.

def home(request):
    return render(request,'home.html')

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid credentials')
            return render(request, 'login.html')
    elif request.user.is_authenticated:
        return redirect('/')
    return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        fname = request.POST ['fname']
        lname = request.POST ['lname']
        email = request.POST['email']
        phone = request.POST ['phone']
        age = request.POST ['age']
        address = request.POST ['address']
        zone = request.POST ['zone']
        blood = request.POST ['blood']
        gender =request.POST['gender']

        password = request.POST['password']
        if User.objects.filter(username=email).exists():
            messages.info(request,'Email already in use') ###
            return render(request,'register.html')
        else:
            user = User.objects.create_user(first_name = fname, last_name = lname, email=email,password=password,username=email, is_staff = True)
            profile = UserProfile.objects.create(user=user, phone_number=phone, age=age, address=address, gender=gender, zone = zone, blood=blood)

            #login
            user = auth.authenticate(username=email, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect('/')

    elif request.user.is_authenticated:
        return redirect('/')
    return render(request,'register.html')

def logout(request):
    auth.logout(request)
    return redirect('/')

def profile(request):
    if user_logged_in:
        profile = UserProfile.objects.filter(user_id = request.user.id)
        return render(request, 'user_profile.html', {'profile_info': profile})
def dashboard(request):
    if user_logged_in:
        return render(request,'dashboard.html')

def about(request):
    return render(request, 'about.html')

def update_bank(zone, blood_type, quantity):
    blood_bank = BloodBankInfo.objects.get(branch_zone=zone)
    if blood_type == 'A+':
        blood_bank.a_positive += quantity
    elif blood_type == 'A-':
        blood_bank.a_negative += quantity
    elif blood_type == 'B+':
        blood_bank.b_positive += quantity
    elif blood_type == 'B-':
        blood_bank.b_negative += quantity
    elif blood_type == 'O+':
        blood_bank.o_positive += quantity
    elif blood_type == 'O-':
        blood_bank.o_negative += quantity
    elif blood_type == 'AB+':
        blood_bank.ab_positive += quantity
    elif blood_type == 'AB-':
        blood_bank.ab_negative += quantity

    blood_bank.save()


def entry(request):
    if request.method == 'POST':
        date = request.POST['date']
        blood_type = request.POST['blood_type']
        quantity = request.POST['quantity']
        profile = UserProfile.objects.filter(user_id = request.user.id)
        for working in profile:
            zone = working.working_zone

        #update bank info
        update_bank(zone, blood_type, int(quantity))

        BloodBagInfo.objects.create(blood_group=blood_type, date = date, quantity = quantity, branch = zone)
        return redirect('details')

    return render(request, 'blood_entry.html')

def details(request):
    blood = BloodBankInfo.objects.all()
    return render(request, 'blood_details.html', {'blood_info': blood})

def list(request):
    users = UserProfile.objects.all()
    return render(request, 'user_list.html', {'users': users})

def delete_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_staff = False
    user.save()
    return redirect('list')

def donate(request):
    if request.method == 'POST':
        date = request.POST['date']
        blood_type = request.POST['blood_type']
        quantity = int(request.POST['quantity']) * -1
        profile = UserProfile.objects.filter(user_id = request.user.id)
        for working in profile:
            zone = working.working_zone
        update_bank(zone, blood_type, int(quantity))
        BloodBagInfo.objects.create(blood_group=blood_type, date = date, quantity = quantity, branch = zone)
        return redirect('details')
    return render(request, 'donate.html')

def search(request):
    if request.method == 'POST':
        zone = request.POST['zone']
        blood_group = request.POST['blood_group']
        avail = BloodBankInfo.objects.filter(branch_zone=zone)

        for i in avail:
            if blood_group == 'a_positive':
                count = i.a_positive
                blood = 'A+'
            elif blood_group == 'a_negative':
                count = i.a_negative
                blood = 'A-'
            elif blood_group == 'b_positive':
                count = i.b_positive
                blood = 'B+'
            elif blood_group == 'b_negative':
                count = i.b_negative
                blood = 'B-'
            elif blood_group == 'o_positive':
                count = i.o_positive
                blood = 'O+'
            elif blood_group == 'o_negative':
                count = i.o_negative
                blood = 'O-'
            elif blood_group == 'ab_positive':
                count = i.ab_positive
                blood = 'AB+'
            elif blood_group == 'ab_negative':
                count = i.ab_negative
                blood = 'AB-'

        quantity = int(request.POST['quantity'])
        if quantity<0:
            return  render(request, 'search.html')
        elif quantity<= count:
                available = True
        else:
                available = False


        donors = UserProfile.objects.filter(zone= zone, blood = blood, is_donor = True)
        print(donors)


        return render(request, 'search.html', {'availability': available, 'donors':donors})

    return render(request, 'search.html')


def update_active_status(request, user_id):
    user = UserProfile.objects.get(user_id=user_id)
    user.is_donor = not user.is_donor  # Toggle the status
    user.save()
    return redirect('profile')

