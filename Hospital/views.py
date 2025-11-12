from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,logout,login
from django.contrib.auth.decorators import login_required
from .models import *
from django.db.models import Q
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db.models import Count , Sum
from datetime import datetime ,time , timedelta
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from urllib.parse import quote
import time
import json
# Create your views here.


# Home Page ........................
def About(request):
    doctors = Doctor.objects.all()
    return render(request, "about.html", {"doctors": doctors})

@login_required
def Index(request):
    if not request.user.is_staff:
        return redirect('login')

    # === Totals ===
    doctors = Doctor.objects.count()
    patients = Patient.objects.count()
    appointments = Appointment.objects.count()
    prescriptions = 0  # You can replace this later with your prescription count model

    total = {
        'doctors': doctors,
        'patients': patients,
        'appointments': appointments,
        'prescriptions': prescriptions
    }

    # === Chart Data (Last 7 Days) ===
    today = timezone.now().date()
    labels = []
    values = []
    for i in range(7):
        day = today - timedelta(days=6 - i)
        labels.append(day.strftime("%b %d"))
        count = Appointment.objects.filter(Date1=day).count()
        values.append(count)

    # === Recent Appointments ===
    recent_appointments = Appointment.objects.order_by('-Date1', '-Time1')[:6]

    context = {
        'total': total,
        'chart_labels': json.dumps(labels),
        'chart_values': json.dumps(values),
        'recent_appointments': recent_appointments,
    }

    return render(request, 'index.html', context)


def book_appointment(request):
    doctors = Doctor.objects.all()

    if request.method == "POST":
        doctor_id = request.POST.get("D_name")
        patient_name = request.POST.get("P_name")
        date_str = request.POST.get("date")
        time_str = request.POST.get("time")

        if not doctor_id:
            messages.error(request, "Please select a doctor.")
            return redirect('add_appointment')

        doctor = Doctor.objects.get(id=doctor_id)

        # Create or get patient by name
        patient, created = Patient.objects.get_or_create(name=patient_name, defaults={
            "Age": 0,
            "Gender": "Not Provided",
            "Mobile": 0,
            "Address": ""
        })

        # Convert date/time to objects
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        time_obj = datetime.strptime(time_str, "%H:%M").time()

        # Fetch schedule for the selected date (or Daily schedule fallback)
        schedule = DoctorSchedule.objects.filter(doctor=doctor, date=date_obj).first()

        if not schedule:
            schedule = DoctorSchedule.objects.filter(doctor=doctor, schedule_type="Daily").first()

        if not schedule:
            messages.error(request, f"No schedule found for {doctor.name}. Cannot book appointment.")
            return redirect('add_appointment')

        # Save appointment
        Appointment.objects.create(
            Doctor=doctor,
            Patient=patient,
            Date1=date_obj,
            Time1=time_obj,
            Schedule=schedule,
            created_by=request.user,
        )

        messages.success(request, "✅ Appointment booked successfully!")
        return redirect('view_Appointment')

    return render(request, "add_appointment.html", {"doctors": doctors})


def get_doctor_schedule(request, doctor_id, date):
    doctor = Doctor.objects.get(id=doctor_id)

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except:
        return JsonResponse({"status": "no_schedule"})

    # First try schedule for selected date
    schedule = DoctorSchedule.objects.filter(doctor=doctor, date=date_obj).first()

    # If none, fallback to Daily schedule
    if not schedule:
        schedule = DoctorSchedule.objects.filter(doctor=doctor, schedule_type="Daily").first()

    if not schedule:
        return JsonResponse({"status": "no_schedule"})

    start_dt = datetime.combine(date_obj, schedule.start_time)
    end_dt = datetime.combine(date_obj, schedule.end_time)
    step = timedelta(minutes=30)

    slots = []
    while start_dt <= end_dt:
        slots.append(start_dt.strftime("%H:%M"))
        start_dt += step

    return JsonResponse({
        "status": "ok",
        "start_time": schedule.start_time.strftime("%I:%M %p"),
        "end_time": schedule.end_time.strftime("%I:%M %p"),
        "slots": slots
    })


def Admin_Login(request):
    error=""
    if request.method=='POST':
        u = request.POST['name']
        p = request.POST['pass']
        user = authenticate(username=u , password=p)
        try:
            if user.is_staff:
                login(request , user)
                error="no"
            else:
                error="yes"
        except:
            error = "yes"
            
    
    return render(request , 'admin_login.html' , {'error':error})

def Admin_Logout(request):
    if not request.user.is_staff:
        return redirect('login')
    logout(request)
    return redirect('home')

def Home(request):
    return render(request,'home.html')

def Contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        full_message = f"""
From: {name}
Email: {email}

Message:
{message}
"""

        send_mail(
            subject,
            full_message,
            settings.EMAIL_HOST_USER,   # sender (your email)
            ["amanlaha20@gmail.com"],   # receiver (your email)
            fail_silently=False,
        )

        messages.success(request, "✅ Your message has been sent successfully.")
        return render(request, "contact.html")

    return render(request, "contact.html")




# ...........................................

# Doctor part ...............................

def view_doctor(request):
    if not request.user.is_staff:
        return redirect('login')
    doc = Doctor.objects.all()
    d={'doc':doc}
    return render(request , 'view_doctor.html' , d)

def Add_doctor(request):
    if not request.user.is_staff:
        return redirect('login')
    error=""
    if request.method=='POST':
        n = request.POST.get('name')
        c = request.POST.get('contact')
        sp = request.POST.get('specialization')
        q = request.POST.get('qualification')
        exp = request.POST.get('experience')
        g = request.POST.get('gender')
        add = request.POST.get('address')
        img = request.FILES.get('image')
        
        try:
            Doctor.objects.create(
                name=n ,
                Mobile=c , 
                Special=sp,
                qualification=q,
                experience=exp,
                gender=g,
                address=add,
                image=img
            )
            messages.success(request, "Doctor added successfully!")
            return redirect('view_doctor')   
            error="no"
            
        except Exception as e:
            print("Error adding doctor: " ,e)
            error = "yes"
            
    
    return render(request , 'add_doctor.html' , {'error':error})

def edit_doctor(request,id):
    if not request.user.is_staff:
        return redirect('login')
    
    doctor = Doctor.objects.get(id=id)
    error=""
    
    if request.method=='POST':
        doctor.name = request.POST.get('name')
        doctor.Mobile = request.POST.get('contact')
        doctor.Special = request.POST.get('specialization')
        doctor.qualification = request.POST.get('qualification')
        doctor.experience = request.POST.get('experience')
        doctor.gender = request.POST.get('gender')
        doctor.address = request.POST.get('address')
        
        if request.FILES.get('image'):
            doctor.image = request.FILES.get('image')
            
        try:
            doctor.save()
            messages.success(request,"Doctor updated successfully!")
            return redirect('view_doctor')
        
        except Exception as e:
            print("Error updating doctor:" , e)
            error="yes"
    return render(request,'edit_doctor.html',{'doctor':doctor , 'error':error})

def manage_schedule(request):
    if not request.user.is_staff:
        return redirect('login')

    doctors = Doctor.objects.all()
    schedules = DoctorSchedule.objects.select_related('doctor').order_by('-date', 'doctor__name')

    if request.method == 'POST':
        doctor_id     = request.POST.get('doctor_id')
        date          = request.POST.get('date')
        start_time    = request.POST.get('start_time')
        end_time      = request.POST.get('end_time')
        schedule_type = request.POST.get('schedule_type', 'Daily')
        booking_start = request.POST.get('booking_start') or None
        booking_end   = request.POST.get('booking_end') or None

        doctor = Doctor.objects.filter(id=doctor_id).first()
        if not doctor:
            messages.error(request, "Invalid doctor selected.")
            return redirect('manage_doctor')

        # Prevent overlapping schedule for same doctor & date
        overlap = DoctorSchedule.objects.filter(
            doctor=doctor, date=date,
            start_time__lt=end_time, end_time__gt=start_time
        ).exists()
        if overlap:
            messages.error(request, "This schedule overlaps an existing schedule for that date.")
            return redirect('manage_doctor')

        # Parse custom times if provided
        bs = datetime.fromisoformat(booking_start) if (booking_start and schedule_type == 'Custom') else None
        be = datetime.fromisoformat(booking_end) if (booking_end and schedule_type == 'Custom') else None

        DoctorSchedule.objects.create(
            doctor=doctor,
            date=date,
            start_time=start_time,
            end_time=end_time,
            schedule_type=schedule_type,
            booking_start=bs,
            booking_end=be
        )
        messages.success(request, "Schedule added successfully.")
        return redirect('manage_doctor')

    return render(request, 'manage_schedule.html', {
        'doctors': doctors,
        'schedules': schedules
    })

    
def edit_schedule(request, id):
    if not request.user.is_staff:
        return redirect('login')

    schedule = get_object_or_404(DoctorSchedule, id=id)
    doctors = Doctor.objects.all()

    if request.method == 'POST':
        doctor_id     = request.POST.get('doctor_id')
        date          = request.POST.get('date')
        start_time    = request.POST.get('start_time')
        end_time      = request.POST.get('end_time')
        schedule_type = request.POST.get('schedule_type', 'Daily')
        booking_start = request.POST.get('booking_start') or None
        booking_end   = request.POST.get('booking_end') or None

        doc = Doctor.objects.filter(id=doctor_id).first()
        if not doc:
            messages.error(request, "Invalid doctor.")
            return redirect('manage_doctor')

        # Prevent overlapping with others (excluding this one)
        overlap = DoctorSchedule.objects.filter(
            doctor=doc, date=date,
            start_time__lt=end_time, end_time__gt=start_time
        ).exclude(id=schedule.id).exists()
        if overlap:
            messages.error(request, "This schedule overlaps an existing schedule.")
            return redirect('manage_doctor')

        schedule.doctor = doc
        schedule.date = date
        schedule.start_time = start_time
        schedule.end_time = end_time
        schedule.schedule_type = schedule_type

        if schedule_type == 'Custom':
            schedule.booking_start = datetime.fromisoformat(booking_start) if booking_start else None
            schedule.booking_end   = datetime.fromisoformat(booking_end) if booking_end else None
        else:
            schedule.booking_start = None
            schedule.booking_end   = None

        schedule.save()
        messages.success(request, "Schedule updated successfully.")
        return redirect('manage_doctor')

    return render(request, 'edit_schedule.html', {
        'schedule': schedule,
        'doctors': doctors
    })


def delete_schedule(request,id):
    if not request.user.is_staff:
        return redirect('login')
    
    try:
        schedule = DoctorSchedule.objects.get(id=id)
        schedule.delete()
        messages.success(request,"Schedule deleted successfully.")
        
    except Exception as e:
        messages.error(request,"Schedule not found")
        
    return redirect('manage_doctor')

   
def delete_doctor(request,id):
    if not request.user.is_staff:
        return redirect('login')
    doctor = Doctor.objects.get(id=id)
    doctor.delete()
    return redirect('view_doctor')


# ...........................................................

# Patient part ...................................................

def Add_patient(request):
    if not request.user.is_staff:
        return redirect('login')
    error=""
    if request.method=='POST':
        n = request.POST['name']
        a = request.POST['age']
        g = request.POST['gender']
        m = request.POST['mobile']
        Address =request.POST['address']
        
        try:
            Patient.objects.create(name=n , Age=a, Gender=g, Mobile=m , Address=Address)   
            error="no"
            
        except:
            error = "yes"
            
    
    return render(request , 'add_patient.html' , {'error':error})

def view_patient(request):
    if not request.user.is_staff:
        return redirect('login')
    poc = Patient.objects.all()
    p={'poc':poc}
    return render(request , 'view_patient.html' , p)


def delete_patient(request,id):
    if not request.user.is_staff:
        return redirect('login')
    patient = Patient.objects.get(id=id)
    patient.delete()
    return redirect('view_patient')

@login_required
def view_Appointments_admin(request):
    query = request.GET.get('q', '').strip()
    doctor_filter = request.GET.get('doctor', '')
    date_filter = request.GET.get('date', '')
    status_filter = request.GET.get('status', '')

    appointments = Appointment.objects.all().order_by('-Date1', '-Time1')

    # ✅ Apply search filter
    if query:
        appointments = appointments.filter(
            Q(Doctor__name__icontains=query) |
            Q(Patient__name__icontains=query) |
            Q(Date1__icontains=query)
        )

    # ✅ Apply doctor filter
    if doctor_filter:
        appointments = appointments.filter(Doctor_id=doctor_filter)

    # ✅ Apply date filter
    if date_filter:
        appointments = appointments.filter(Date1=date_filter)

    # ✅ Apply status filter (using the auto status() method)
    if status_filter:
        appointments = [a for a in appointments if a.status() == status_filter]

    context = {
        'appointments': appointments,
        'doctors': Doctor.objects.all(),
        'patients': Patient.objects.all(),
        'query': query,
        'doctor_filter': doctor_filter,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'statuses': ['Upcoming', 'Ongoing', 'Completed'],
    }
    return render(request, 'view_appointments_admin.html', context)

@login_required
def edit_appointment(request, pid):
    appt = Appointment.objects.get(id=pid)
    doctors = Doctor.objects.all()
    patients = Patient.objects.all()

    if request.method == "POST":
        appt.Doctor_id = request.POST.get("doctor")
        appt.Patient_id = request.POST.get("patient")
        appt.Date1 = request.POST.get("date")
        appt.Time1 = request.POST.get("time")
        appt.save()
        messages.success(request, "✅ Appointment updated successfully!")
        return redirect('view_Appointment')

    return render(request, 'edit_appointment.html', {'appt': appt, 'doctors': doctors, 'patients': patients})
def get_available_slots(request):
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'slots': []})

    # Parse date string
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({'slots': []})

    # ✅ Get doctor's schedule for that date
    schedule = DoctorSchedule.objects.filter(doctor_id=doctor_id, date=date_obj).first()
    if not schedule:
        return JsonResponse({'slots': []})

    # ✅ Generate slots every 30 minutes
    slot_duration = timedelta(minutes=30)
    start_dt = datetime.combine(date_obj, schedule.start_time)
    end_dt = datetime.combine(date_obj, schedule.end_time)

    all_slots = []
    while start_dt < end_dt:
        all_slots.append(start_dt.strftime("%H:%M"))
        start_dt += slot_duration

    # ✅ Remove already booked slots
    booked_slots = Appointment.objects.filter(
        Doctor_id=doctor_id,
        Date1=date_obj
    ).values_list('Time1', flat=True)

    booked_formatted = [t.strftime("%H:%M") for t in booked_slots]
    available_slots = [s for s in all_slots if s not in booked_formatted]

    return JsonResponse({'slots': available_slots})

def delete_appointment(request,id):
    if not request.user.is_staff:
        return redirect('login')
    appointment = Appointment.objects.get(id=id)
    appointment.delete()
    return redirect('view_Appointment')

from datetime import datetime
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404

def Add_Appointment(request):
    doctors = Doctor.objects.all()

    if request.method == "POST":
        doctor_id = request.POST.get("D_name")
        patient_name = request.POST.get("P_name")
        date_str = request.POST.get("date")
        time_str = request.POST.get("time")

        # Doctor must be selected
        if not doctor_id:
            messages.error(request, "Please select a doctor.")
            return redirect("add_appointment")

        # This ensures doctor will never be None
        doctor = get_object_or_404(Doctor, id=int(doctor_id))

        # Create or reuse patient by name
        patient, created = Patient.objects.get_or_create(
            name=patient_name,
            defaults={"Age": 0, "Gender": "Not Provided", "Mobile": 0, "Address": ""}
        )

        # Convert date/time properly
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        time_obj = datetime.strptime(time_str, "%H:%M").time()

        # Schedule search (date first → daily fallback)
        schedule = DoctorSchedule.objects.filter(doctor=doctor, date=date_obj).first()
        if not schedule:
            schedule = DoctorSchedule.objects.filter(doctor=doctor, schedule_type="Daily").first()

        if not schedule:
            messages.error(request, f"No schedule created for {doctor.name}. Cannot book appointment.")
            return redirect("add_appointment")

        # Save Appointment
        Appointment.objects.create(
            Doctor=doctor,
            Patient=patient,
            Date1=date_obj,
            Time1=time_obj,
            Schedule=schedule,
            created_by=request.user,
        )

        messages.success(request, "✅ Appointment added successfully!")
        return redirect("view_Appointment")

    return render(request, "add_appointment.html", {"doctors": doctors})

# =========================================================
# 1️⃣  Admin: Add a new patient slip
# =========================================================
def add_patient_slip(request):
    if not request.user.is_staff:
        return redirect('login')
    
    doctors = Doctor.objects.all()

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        doctor = Doctor.objects.filter(id=doctor_id).first()

        slip = PatientSlip.objects.create(
            doctor=doctor,  # <-- save doctor into slip
            patient_name=request.POST.get('patient_name'),
            age=request.POST.get('age'),
            gender=request.POST.get('gender'),
            mobile=request.POST.get('mobile'),
            blood_pressure=request.POST.get('blood_pressure'),
            pulse=request.POST.get('pulse'),
            weight=request.POST.get('weight'),
            fbs=request.POST.get('fbs'),
            pbs=request.POST.get('pbs'),
            amount=request.POST.get('amount') or 0
        )

        # ✅ Redirect with query param
        return redirect('print_slip' , id=slip.id)

    return render(request, 'add_patient_slip.html', {'doctors': doctors})



from django.utils.timezone import localdate, localtime
from datetime import datetime, time
from django.shortcuts import render, get_object_or_404

def print_slip(request, id):
    slip = get_object_or_404(PatientSlip, id=id)
    doctor = slip.doctor
    store = StoreDesign.objects.first()

    # ✅ Get the slip's date in local India date (no timezone mismatch)
    slip_day = localdate(slip.date)

    # ✅ Create start & end timestamps for that day in IST
    day_start = datetime.combine(slip_day, time.min)
    day_end   = datetime.combine(slip_day, time.max)

    # ✅ Perfect filter: same doctor + same Indian date range
    same_day_slips = PatientSlip.objects.filter(
        doctor=doctor,
        date__gte=day_start,
        date__lte=day_end
    ).order_by('date', 'id')

    # ✅ Serial number = count slips earlier or equal
    serial = same_day_slips.filter(date__lte=slip.date).count()

    return render(request, 'print_slip.html', {
        'slip': slip,
        'doctor': doctor,
        'store': store,
        'serial': serial,
    })



# ======================= PRESCRIPTION (MANUAL ENTRY) =======================
def create_prescription(request):
    if not request.user.is_staff:
        return redirect('login')

    doctors = Doctor.objects.all()
    store = StoreDesign.objects.first() or StoreDesign.objects.create()

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        patient_name = request.POST.get('patient_name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        mobile = request.POST.get('mobile')
        bp = request.POST.get('bp')
        pulse = request.POST.get('pulse')
        weight = request.POST.get('weight')
        fbs = request.POST.get('fbs')
        pbs = request.POST.get('pbs')
        amount = request.POST.get('amount')

        doctor = Doctor.objects.get(id=doctor_id)

        context = {
            'doctor': doctor,
            'store': store,
            'data': {
                'patient_name': patient_name,
                'age': age,
                'gender': gender,
                'mobile': mobile,
                'bp': bp,
                'pulse': pulse,
                'weight': weight,
                'fbs': fbs,
                'pbs': pbs,
                'amount': amount
            }
        }
        return render(request, 'prescription_print.html', context)

    return render(request, 'create_prescription.html', {'doctors': doctors, 'store': store})

def edit_store_design(request):
    if not request.user.is_staff:
        return redirect('login')

    store = StoreDesign.objects.first()
    if not store:
        store = StoreDesign.objects.create()

    if request.method == "POST":
        store.store_name = request.POST.get('store_name')
        store.address = request.POST.get('address')
        store.phone_numbers = request.POST.get('phone_numbers')
        store.doctor_name = request.POST.get('doctor_name')
        store.qualification = request.POST.get('qualification')
        store.hospital_info = request.POST.get('hospital_info')
        store.consultation_info = request.POST.get('consultation_info')
        store.reg_no = request.POST.get('reg_no')
        store.footer_note = request.POST.get('footer_note')

        if request.FILES.get('logo'):
            store.logo = request.FILES.get('logo')

        store.save()
        messages.success(request, "✅ Store design updated successfully!")

    return render(request, 'edit_store_design.html', {'store': store})


# 🧩 NEW: Preview Design View
def preview_store_design(request):
    """Shows a live preview of the current store design using a sample slip."""
    store = StoreDesign.objects.first()
    if not store:
        store = StoreDesign.objects.create()

    # Dummy patient slip for preview
    dummy_slip = {
        'patient_name': 'John Doe',
        'age': 45,
        'gender': 'Male',
        'mobile': '9876543210',
        'blood_pressure': '120/80',
        'pulse': '72 bpm',
        'weight': '70 kg',
        'fbs': '95 mg/dl',
        'pbs': '130 mg/dl',
        'next_visit': '15 Nov 2025',
        'amount': 450.00
    }

    return render(request, 'preview_store_design.html', {'store': store, 'slip': dummy_slip})


def user_register(request):
    error = ""
    if request.method == 'POST':
        name = request.POST['name']
        age = request.POST['age']
        gender = request.POST['gender']
        mobile = request.POST['mobile']
        address = request.POST['address']
        password = request.POST['password']
        picture = request.FILES.get('picture')

        try:
            # Check if user already exists
            if User.objects.filter(username=mobile).exists():
                error = "exists"
            else:
                # Create Django user
                user = User.objects.create_user(username=mobile, password=password, first_name=name)
                user.is_staff = False
                user.save()

                # Create patient profile
                Patient.objects.create(user=user,name=name, Age=age, Gender=gender, Mobile=mobile, Address=address , Picture=picture)

                return redirect('user-login')  # Redirect to login page
        except Exception as e:
            print("Error:", e)
            error = "yes"

    return render(request, 'user-register.html', {'error': error})

def user_home(request):
    return render(request,'user_home.html')

def user_login(request):
    error = ""
    if request.method == 'POST':
        mobile = request.POST['mobile']
        password = request.POST['password']

        user = authenticate(username=mobile, password=password)
        if user:
            login(request, user)
            return redirect('user-home')
        else:
            error = "invalid"

    return render(request, 'user-login.html', {'error': error})


def user_profile(request):
    if not request.user.is_authenticated:
        return redirect('user_register')

    patient = Patient.objects.get(user=request.user)
    return render(request, 'user-profile.html', {'patient': patient})

def user_edit_profile(request):
    if not request.user.is_authenticated:
        return redirect('user_register')

    patient = Patient.objects.get(user=request.user)

    if request.method == 'POST':
        patient.name = request.POST.get('name')
        patient.Age = request.POST.get('age')
        patient.Gender = request.POST.get('gender')
        patient.Address = request.POST.get('address')
        patient.Mobile = request.POST.get('mobile')

        if request.FILES.get('picture'):
            patient.Picture = request.FILES.get('picture')

        patient.save()

        # Also update Django User model (name shown in top nav)
        user = request.user
        user.first_name = patient.name
        user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('user-profile')

    return render(request, 'user-edit-profile.html', {'patient': patient})


def user_logout(request):
    if not request.user.is_authenticated:
        return redirect('user_register')
    logout(request)
    return redirect('home')


def user_appointment(request):
    if not request.user.is_authenticated:
        return redirect('user-register')

    schedule_id = request.GET.get('schedule_id') or request.POST.get('schedule_id')
    schedule = DoctorSchedule.objects.filter(id=schedule_id).first()
    
    if not schedule:
        messages.error(request,"Invalid schedule seleted .")
        return redirect('view_doctors')
    
    now = timezone.localtime()
    if schedule.booking_start and schedule.booking_end:
        if not (schedule.booking_start <= now <= schedule.booking_end):
            messages.error(request,"Booking is not open for this schedule.")
            return redirect('view_doctor')
    
    doctor=schedule.doctor
    logged_in_patient = Patient.objects.filter(user=request.user).first()
    
    if request.method =='POST':
        booking_type = request.POST.get('booking_type')
        
        if booking_type =="self":
            patient=logged_in_patient
            
        else:
            name = request.POST.get('name')
            age = request.POST.get('age')
            gender = request.POST.get('gender')
            address = request.POST.get('address')
            mobile = request.POST.get('mobile')
            
            patient = Patient.objects.filter(Mobile=mobile).first()
            
            if not patient:
            
                patient=Patient.objects.create(
                            user=None,
                            name=name,
                            Age=age,
                            Gender=gender,
                            Address=address,
                            Mobile=mobile
                        )
        try:
            Appointment.objects.create(
                Doctor=doctor,
                Patient=patient,
                Date1=schedule.date,
                Time1=schedule.start_time,
                Schedule=schedule,
                created_by=request.user
            )
            messages.success(request, 'Appointment booked successfully.')
            return redirect('user_status')
        except Exception as e:
            print("Error creating appointment:", e)
            messages.error(request, 'Something went wrong. Try again.')

    return render(request, 'user-appointment.html', {'doctor': doctor, 'schedule': schedule , 'schedule_id':schedule_id , 'logged_in_patient':logged_in_patient})


def view_doctors(request):
    doctors = Doctor.objects.all()
    doctor_data = []
    now = timezone.localtime()

    for doctor in doctors:
        
        daily_schedule = DoctorSchedule.objects.filter(doctor=doctor, schedule_type="Daily").first()
        dated_schedules = DoctorSchedule.objects.filter(doctor=doctor, schedule_type="Custom").order_by('date')

        schedules = []
        if daily_schedule:
            schedules.append(daily_schedule)
        schedules.extend(list(dated_schedules))

        schedule_list = []

        for sch in schedules:

            if sch.schedule_type == "Custom":
                schedule_end_dt = datetime.combine(sch.date, sch.end_time)
                schedule_end_dt = timezone.make_aware(schedule_end_dt)

                if now > schedule_end_dt + timedelta(hours=4):
                    continue

            already_booked = Appointment.objects.filter(Schedule=sch).exists()

            if sch.schedule_type == "Daily":
                status = 'open'
            else:
                if sch.booking_start and sch.booking_end:
                    if now < sch.booking_start:
                        status = 'not_started'
                    elif now > sch.booking_end:
                        status = 'closed'
                    else:
                        status = 'open'
                else:
                    status = 'no_schedule'

            schedule_list.append({
                'id': sch.id,
                'date': sch.date if sch.schedule_type == "Custom" else "Everyday",
                'start_time': sch.start_time,
                'end_time': sch.end_time,
                'booking_start': sch.booking_start,
                'booking_end': sch.booking_end,
                'status': status,
                'already_booked': already_booked
            })

        doctor_data.append({
            'doctor': doctor,
            'schedules': schedule_list
        })

    return render(request, 'view_doctors.html', {'doctor_data': doctor_data})


def user_status(request):
    if not request.user.is_authenticated:
        return redirect('user-register')

    now = timezone.now().date()   # current date

    appointments = Appointment.objects.filter(
        created_by=request.user,
        Date1__gte=now  # Only appointments today or future
    ).order_by('Date1', 'Time1')

    # Calculate waiting position for each appointment
    appointment_data = []
    for app in appointments:
        waiting_count = Appointment.objects.filter(
            Doctor=app.Doctor,
            Date1=app.Date1,
            Time1=app.Time1,
            id__lt=app.id
        ).count() + 1

        appointment_data.append({
            'appointment': app,
            'waiting': waiting_count
        })

    return render(request, 'user-status.html', {'appointment_data': appointment_data})

def user_history(request):
    if not request.user.is_authenticated:
        return redirect('user-register')
    
    appointments = Appointment.objects.filter(
        created_by=request.user
    ).order_by('-Date1' , '-Time1')
    
    return render(request, 'user-history.html',{'appointments':appointments})

def contact_doctor(request):
    return render(request, 'contact.html')

def profile_settings(request):
    return render(request,'profile_settings.html')

from django.db.models.functions import TruncDate
from django.db.models import Sum
from django.db.models.functions import TruncDate
from datetime import datetime

from django.db.models import Sum
from datetime import datetime

from datetime import datetime

def daily_collection(request):
    doctors = Doctor.objects.all()
    slips = PatientSlip.objects.all()

    doctor_id = request.GET.get("doctor_id")
    date_str = request.GET.get("date")
    print("DATE RECEIVED:", date_str)

    # Filter by doctor
    if doctor_id:
        slips = slips.filter(doctor_id=doctor_id)

    # Filter by date (Correct Way)
    if date_str:
        date_obj=None
        date_str = date_str.replace('/','-')
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            try:
                date_obj = datetime.strptime(date_str, "%d-%m-%Y").date()
            except:
                pass
        
        # Apply filter only if conversion succeeded
        if date_obj:
            start = datetime.combine(date_obj, datetime.min.time())
            end = start + timedelta(days=1)
            slips = slips.filter(date__gte=start, date__lt=end)
        else:
            slips = slips.none()

    slips = slips.order_by("-date")
    total_amount = slips.aggregate(total=Sum("amount"))["total"] or 0

    print("SLIP COUNT:", slips.count())

    return render(request, "daily_collection.html", {
        "doctors": doctors,
        "slips": slips,
        "total_amount": total_amount,
        "selected_doctor": doctor_id,     # ✅ add this
        "selected_date": date_str,        # ✅ add this
    })



from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse
from django.utils.timezone import make_aware, localdate
from datetime import datetime, time, timedelta

def daily_collection_pdf(request):
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    slips = PatientSlip.objects.select_related('doctor').order_by('date', 'id')

    # ✅ Safe doctor filter (no error if None or blank)
    if doctor_id and doctor_id.isdigit():
        slips = slips.filter(doctor_id=int(doctor_id))

    # ✅ Convert date input safely
    date_obj = None
    if date_str and date_str not in ["", "None"]:
        date_str = date_str.replace("/", "-")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            try:
                date_obj = datetime.strptime(date_str, "%d-%m-%Y").date()
            except:
                date_obj = None

    # ✅ Correct timezone-safe filtering for selected day
    if date_obj:
        start = make_aware(datetime.combine(date_obj, time.min))
        end = make_aware(datetime.combine(date_obj, time.max))
        slips = slips.filter(date__gte=start, date__lte=end)

    # ✅ Serial number per doctor per day
    serial_map = {}
    final_slips = []
    for s in slips:
        key = (s.doctor_id, localdate(s.date))
        serial_map[key] = serial_map.get(key, 0) + 1
        s.serial = serial_map[key]
        final_slips.append(s)

    total_amount = slips.aggregate(Sum('amount'))['amount__sum'] or 0

    template = get_template('daily_collection_pdf.html')
    html = template.render({'slips': final_slips, 'total_amount': total_amount})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Daily_Collection_Report.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response

# views.py
from datetime import datetime
from django.db.models import Sum


def edit_slip(request, id):
    slip = get_object_or_404(PatientSlip, id=id)
    doctors = Doctor.objects.all()

    if request.method == 'POST':
        slip.doctor_id = request.POST.get('doctor_id')
        slip.patient_name = request.POST.get('patient_name')
        slip.age = request.POST.get('age')
        slip.gender = request.POST.get('gender')
        slip.mobile = request.POST.get('mobile')
        slip.blood_pressure = request.POST.get('blood_pressure')
        slip.pulse = request.POST.get('pulse')
        slip.weight = request.POST.get('weight')
        slip.fbs = request.POST.get('fbs')
        slip.pbs = request.POST.get('pbs')
        slip.amount = request.POST.get('amount')
        slip.save()
        messages.success(request, "Slip updated successfully ✅")
        return redirect('edit_slip' , id=slip.id)

    return render(request, "edit_slip.html", {"slip": slip, "doctors": doctors})


def delete_slip(request, id):
    slip = get_object_or_404(PatientSlip, id=id)
    slip.delete()
    messages.success(request, "Slip deleted successfully.")
    return redirect('daily_collection')


def contact_medicine(request):
    if request.method == "POST":
        Feedback.objects.create(
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            message=request.POST.get("message")
        )
        messages.success(request, "✅ Your message has been sent successfully!")
        return redirect("contact_medicine")

    return render(request, "contact_medicine.html")

@login_required
def admin_feedback_list(request):
    feedbacks = Feedback.objects.all().order_by('-date')
    return render(request, 'admin_feedback_list.html', {"feedbacks": feedbacks})

