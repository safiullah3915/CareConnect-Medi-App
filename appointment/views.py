from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View

from hospital.models import Doctor
from .models import Appointment

from django.http import JsonResponse
from healthcare.serializers import AppointmentSerializer

from rest_framework.decorators import api_view

class AppointmentView(View):
    def get(self, request, *args, **kwargs):
        context = {
            'doctors': Doctor.objects.all()
        }
        return render(request, 'appointment/appointments.html',context)
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            date = request.POST.get('date')
            time = request.POST.get('time')
            extra_note = request.POST.get('extra_note', '')  # Default to empty string if not provided
            doctor_id = request.POST.get('doctor')

        # Initialize doctor to None
            doctor = None

            if doctor_id:
                doctor = get_object_or_404(Doctor, id=doctor_id)

            # Collect missing fields
            missing_fields = []
            if not name:
                missing_fields.append('name')
            if not phone:
                missing_fields.append('phone')
            if not email:
                missing_fields.append('email')
            if not doctor:
                missing_fields.append('doctor')
            if not date:
                missing_fields.append('date')
            if not time:
                missing_fields.append('time')

            # Return detailed error response if there are missing fields
            if missing_fields:
                return JsonResponse({'error': 'Missing fields', 'missing': missing_fields}, status=400)

            # Create the appointment
            Appointment.objects.create(
                name=name,
                phone=phone,
                email=email,
                doctors=doctor,
                extra_note=extra_note,
                time=time,
                date=date
            )
            messages.success(request, 'Appointment done successfully')
            return redirect('appointment')
    
@api_view(['GET'])  
def appointment_list(request, *args, **kwargs):

    if request.method == 'GET':
        appointments = Appointment.objects.all()
        serializer = AppointmentSerializer(appointments, many=True)
        return JsonResponse({'appointments': serializer.data}, safe=False)