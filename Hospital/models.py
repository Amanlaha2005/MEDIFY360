from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Appointment1(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    department = models.CharField(max_length=100)
    date = models.DateField()
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.department}"

class Doctor(models.Model):
    name = models.CharField(max_length=50)
    Mobile = models.BigIntegerField()
    Special = models.CharField(max_length=50)
    qualification = models.CharField(max_length=100 , null=True , blank=True)
    experience = models.CharField(max_length=50, null=True , blank=True)
    gender = models.CharField(max_length=10,null=True , blank=True)
    address = models.TextField(null=True,blank=True)
    image = models.ImageField(upload_to='doctor_image/', null=True , blank=True)
    
    def __str__(self):
        return f"Dr. {self.name} ({self.Special})"


class Patient(models.Model):
    user = models.OneToOneField(User , on_delete=models.CASCADE , null=True )
    name = models.CharField(max_length=80)
    Age = models.IntegerField()
    Gender = models.CharField(max_length=10)
    Mobile = models.BigIntegerField(null=True)
    Address = models.CharField(max_length=300)
    Picture = models.ImageField(upload_to='patient_pics/' , null=True , blank=True)
    def __str__(self):
        return self.name
    
class DoctorSchedule(models.Model):
    SCHEDULE_TYPES = (('Daily', 'Daily'), ('Custom', 'Custom'))

    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    
    schedule_type = models.CharField(max_length=10, choices=SCHEDULE_TYPES, default='Daily')
    booking_start = models.DateTimeField(null=True, blank=True)
    booking_end   = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.doctor.name} - {self.date} ({self.start_time} to {self.end_time})"

    def is_booking_open(self):
        """
        - Daily  : always open
        - Custom : open only within booking_start..booking_end
        """
        if self.schedule_type == 'Daily':
            return True
        if self.booking_start and self.booking_end:
            now = timezone.localtime()
            return self.booking_start <= now <= self.booking_end
        return False

    
class Appointment(models.Model):
    Doctor = models.ForeignKey(Doctor,on_delete=models.CASCADE)
    Patient = models.ForeignKey(Patient,on_delete=models.CASCADE)
    Date1 = models.DateField()
    Time1 = models.TimeField()
    Schedule = models.ForeignKey(DoctorSchedule , on_delete=models.SET_NULL , null=True , blank=True)
    created_by = models.ForeignKey(User , on_delete=models.CASCADE , null=True , blank=True)
    
    
    
    def __str__(self):
        return f"{self.Doctor.name} -- {self.Patient.name}"
    
    def status(self):
        """Return automatic appointment status."""
        from datetime import datetime, timedelta
        now = datetime.now()
        appointment_datetime = datetime.combine(self.Date1, self.Time1)
        if now < appointment_datetime:
            return "Upcoming"
        elif appointment_datetime <= now <= appointment_datetime + timedelta(hours=4):
            return "Ongoing"
        else:
            return "Completed"

    
class PatientSlip(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    patient_name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    mobile = models.CharField(max_length=15)
    blood_pressure = models.CharField(max_length=20, blank=True, null=True)
    pulse = models.CharField(max_length=20, blank=True, null=True)
    weight = models.CharField(max_length=20, blank=True, null=True)
    fbs = models.CharField(max_length=20, blank=True, null=True)
    pbs = models.CharField(max_length=20, blank=True, null=True)
    next_visit = models.CharField(max_length=50, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.patient_name


class StoreDesign(models.Model):
    store_name = models.CharField(max_length=150, default="MAA MEDICINE STORE")
    address = models.CharField(max_length=200, default="STATION BAZAR, JAJPUR ROAD")
    phone_numbers = models.CharField(max_length=100, default="9861182055, 8637219213")
    footer_note = models.CharField(max_length=200, blank=True, null=True)
    logo = models.ImageField(upload_to='store_logos/', null=True, blank=True)

    def __str__(self):
        return self.store_name

class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date.strftime('%d-%m-%Y %H:%M')}"