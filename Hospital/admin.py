from django.contrib import admin
from .models import Doctor, Patient, Appointment, DoctorSchedule

# Register models
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(Appointment)
admin.site.register(DoctorSchedule)
