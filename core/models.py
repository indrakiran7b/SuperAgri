from django.db import models
from django.contrib.auth.models import User

class Farm(models.Model):
    SOIL_CHOICES = [
        ('clay', 'Clay'),
        ('loam', 'Loam'),
        ('sandy', 'Sandy'),
        ('silt', 'Silt'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)
    total_area = models.DecimalField(max_digits=10, decimal_places=2)
    soil_type = models.CharField(max_length=50, choices=SOIL_CHOICES)
    previous_crop = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Farm - {self.location}"

class CropPlan(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    crop_name = models.CharField(max_length=100)
    planting_date = models.DateField()
    harvest_date = models.DateField()
    daily_plan = models.JSONField(default=dict)
    pesticides = models.JSONField(default=dict)
    monitoring_frequency = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.crop_name} - {self.farm.location}"


class MonitoringSchedule(models.Model):
    crop_plan = models.ForeignKey('CropPlan', on_delete=models.CASCADE)
    date = models.DateField()
    task_type = models.CharField(max_length=50)  # irrigation, fertilization, pest_check, etc.
    description = models.TextField()
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['date']

class PestAlert(models.Model):
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE)
    pest_name = models.CharField(max_length=100)
    risk_level = models.CharField(max_length=20)  # low, medium, high
    detection_date = models.DateField(auto_now_add=True)
    description = models.TextField()
    recommended_action = models.TextField()
    resolved = models.BooleanField(default=False)

# core/models.py
class CropRecommendation(models.Model):
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Analysis Sections
    climate_description = models.TextField()
    soil_description = models.TextField()
    previous_crop_impact = models.TextField()
    water_analysis = models.TextField(null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Recommendations for {self.farm.location} - {self.created_at.date()}"

class RecommendedCrop(models.Model):
    OPTION_CHOICES = [
        ('1', 'Option 1: Focus on Pulses'),
        ('2', 'Option 2: Diversified Approach'),
    ]

    recommendation = models.ForeignKey(CropRecommendation, on_delete=models.CASCADE, related_name='crops')
    option_number = models.CharField(max_length=1, choices=OPTION_CHOICES)
    crop_name = models.CharField(max_length=100)
    local_name = models.CharField(max_length=100)
    crop_rotation = models.TextField()
    local_adaptation = models.TextField(null=True, blank=True)
    market_demand = models.TextField()
    water_usage = models.TextField(null=True, blank=True)
    growing_season = models.TextField()
    climate = models.TextField(null=True, blank=True)
    maturity = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['option_number', 'id']