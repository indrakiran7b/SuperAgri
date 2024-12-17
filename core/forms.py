# core/forms.py
from django import forms
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone  # Changed this import
from .models import Farm, CropPlan
import re
from datetime import datetime, timedelta

class FarmDetailsForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ['location', 'total_area', 'soil_type', 'previous_crop']
        widgets = {
            'location': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm',
                'placeholder': 'Enter farm location'
            }),
            'total_area': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm',
                'placeholder': 'Enter area in acres',
                'min': '0.1'
            }),
            'soil_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm'
            }),
            'previous_crop': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm',
                'placeholder': 'Enter previous crop name'
            })
        }

    def clean_total_area(self):
        area = self.cleaned_data['total_area']
        if area <= 0:
            raise ValidationError("Area must be greater than 0")
        return area

class CropPlanForm(forms.ModelForm):
    crop_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm',
            'placeholder': 'e.g., Wheat, Rice, Corn',
        })
    )
    
    planting_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm',
            'min': datetime.now().date().isoformat(),  # Fixed this line
        })
    )

    class Meta:
        model = CropPlan
        fields = ['crop_name', 'planting_date']

    def clean_crop_name(self):
        crop_name = self.cleaned_data['crop_name']
        if not re.match(r'^[A-Za-z\s-]+$', crop_name):
            raise ValidationError("Crop name should only contain letters, spaces, and hyphens")
        return crop_name.lower()

    def clean_planting_date(self):
        planting_date = self.cleaned_data['planting_date']
        today = timezone.now().date()
        
        if planting_date < today:
            raise ValidationError("Planting date cannot be in the past")
        
        # Check if date is too far in the future (e.g., 1 year)
        max_future_date = today + timedelta(days=365)
        if planting_date > max_future_date:
            raise ValidationError("Planting date cannot be more than 1 year in the future")
            
        return planting_date

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data