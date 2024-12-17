# views.py
from django.utils import timezone 
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .forms import FarmDetailsForm, CropPlanForm
from .models import Farm, CropPlan, MonitoringSchedule, PestAlert, CropRecommendation
from .utils import (
    generate_crop_plan,
    get_pesticide_recommendations,
    get_crop_recommendation
)
import google.generativeai as genai
from decouple import config
from google.api_core import exceptions as google_exceptions

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('farm_details')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# core/views.py (update the redirects)
# @login_required
# def farm_details(request):
#     try:
#         farm = Farm.objects.get(user=request.user)
#         form = FarmDetailsForm(instance=farm)
#     except Farm.DoesNotExist:
#         form = FarmDetailsForm()

#     if request.method == 'POST':
#         if 'farm' in locals():
#             form = FarmDetailsForm(request.POST, instance=farm)
#         else:
#             form = FarmDetailsForm(request.POST)

#         if form.is_valid():
#             farm = form.save(commit=False)
#             farm.user = request.user
#             farm.save()
#             messages.success(request, 'Farm details saved successfully!')
#             return redirect('core:crop_recommendation')  # Updated
#         else:
#             messages.error(request, 'Please correct the errors below.')

#     return render(request, 'core/farm_details.html', {'form': form})

# @login_required
# def crop_plan(request):
#     if request.method == 'POST':
#         form = CropPlanForm(request.POST)
#         try:
#             if form.is_valid():
#                 crop_plan = form.save(commit=False)
#                 farm = Farm.objects.filter(user=request.user).latest('created_at')
#                 crop_plan.farm = farm
                
#                 # Generate the daily plan
#                 daily_plan = generate_crop_plan(
#                     crop_plan.crop_name,
#                     crop_plan.planting_date,
#                     farm.soil_type
#                 )
#                 crop_plan.daily_plan = daily_plan
                
#                 # Get pesticide recommendations
#                 crop_plan.pesticides = get_pesticide_recommendations(
#                     crop_plan.crop_name,
#                     "initial"
#                 )
                
#                 # Calculate harvest date (simplified)
#                 crop_plan.harvest_date = crop_plan.planting_date + timedelta(days=90)
#                 crop_plan.monitoring_frequency = "weekly"
                
#                 crop_plan.save()
#                 messages.success(request, "Crop plan generated successfully!")
#                 return redirect('core:plan_detail', plan_id=crop_plan.id)  # Updated
#         except ValidationError as e:
#             messages.error(request, str(e))
#         except Exception as e:
#             messages.error(request, "An error occurred. Please try again later.")
#     else:
#         form = CropPlanForm()
    
#     return render(request, 'core/crop_plan.html', {'form': form})

@login_required
def crop_plan(request):
    try:
        farm = Farm.objects.filter(user=request.user).latest('created_at')
    except Farm.DoesNotExist:
        messages.warning(request, "Please add your farm details first.")
        return redirect('core:farm_details')

    if request.method == 'POST':
        form = CropPlanForm(request.POST)
        try:
            if form.is_valid():
                crop_plan = form.save(commit=False)
                crop_plan.farm = farm
                
                try:
                    # Generate the daily plan
                    daily_plan = generate_crop_plan(
                        crop_plan.crop_name,
                        crop_plan.planting_date.strftime('%Y-%m-%d'),
                        farm.soil_type
                    )
                    crop_plan.daily_plan = daily_plan
                    
                    # Calculate harvest date based on the longest phase duration
                    total_days = sum(int(phase.get('duration', '0').split()[0]) 
                                   for phase in daily_plan.get('phases', []))
                    crop_plan.harvest_date = (
                        crop_plan.planting_date + 
                        timedelta(days=total_days if total_days > 0 else 90)
                    )
                    
                    # Set monitoring frequency based on irrigation schedule
                    irrigation_freq = daily_plan.get('irrigation_schedule', {}).get('frequency', 'weekly')
                    crop_plan.monitoring_frequency = irrigation_freq
                    
                    crop_plan.save()
                    messages.success(request, "Crop plan generated successfully!")
                    return redirect('core:plan_detail', plan_id=crop_plan.id)
                    
                except Exception as e:
                    messages.error(request, f"An error occurred while generating the plan. Please try again later.")
                    return render(request, 'core/crop_plan.html', {
                        'form': form,
                        'farm': farm,
                        'error_details': str(e)
                    })
                    
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    else:
        form = CropPlanForm()
    
    return render(request, 'core/crop_plan.html', {
        'form': form,
        'farm': farm
    })

@login_required
def plan_detail(request, plan_id):
    try:
        plan = CropPlan.objects.get(id=plan_id, farm__user=request.user)
        return render(request, 'core/plan_detail.html', {'plan': plan})
    except CropPlan.DoesNotExist:
        messages.error(request, "Crop plan not found.")
        return redirect('crop_plan')
    
def initialize_genai():
    """Initialize the Gemini API with error handling"""
    try:
        api_key = 'AIzaSyDlEMABqE8e29jrqPEX6MhiPHsljw8fEy4'
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.0-flash-exp')
    except Exception as e:
        raise ConnectionError(f"Failed to initialize Gemini API: {str(e)}")

# @login_required
# def crop_recommendation(request):
#     try:
#         farm = Farm.objects.filter(user=request.user).latest('created_at')
        
#         # Initialize Gemini API
#         model = initialize_genai()
        
#         # Generate crop recommendation
#         prompt = f"""Based on the following farm details:
#         Location: {farm.location}
#         Total Area: {farm.total_area} acres
#         Soil Type: {farm.soil_type}
#         Previous Crop: {farm.previous_crop}
        
#         Suggest suitable crops for cultivation considering:
#         1. Local climate and soil conditions
#         2. Crop rotation benefits
#         3. Market value and demand
#         4. Water availability
#         5. Growing season
        
#         Format the response as a structured recommendation with bullet points."""
        
#         try:
#             response = model.generate_content(prompt)
#             recommendations = response.text
#         except google_exceptions.RetryError:
#             messages.error(request, "API service is currently unavailable. Please try again later.")
#             recommendations = "Unable to generate recommendations at this time."
#         except Exception as e:
#             messages.error(request, f"An error occurred while generating recommendations: {str(e)}")
#             recommendations = "Unable to generate recommendations at this time."
        
#         return render(request, 'core/crop_recommendation.html', {
#             'recommendations': recommendations,
#             'farm': farm
#         })
        
#     except Farm.DoesNotExist:
#         messages.warning(request, "Please add your farm details first.")
#         return redirect('core:farm_details')
#     except Exception as e:
#         messages.error(request, f"An unexpected error occurred: {str(e)}")
#         return redirect('core:farm_details')

# core/views.py
# core/views.py
@login_required
def generate_recommendations(request):
    try:
        farm = Farm.objects.filter(user=request.user).latest('created_at')
        
        # Initialize Gemini API
        genai.configure(api_key='AIzaSyDlEMABqE8e29jrqPEX6MhiPHsljw8fEy4')
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""Based on the following farm details:
        Location: {farm.location}
        Total Area: {farm.total_area} acres
        Soil Type: {farm.soil_type}
        Previous Crop: {farm.previous_crop}

        Suggest 3-4 most suitable crops to grow considering:
        1. Local climate conditions
        2. Soil type suitability
        3. Crop rotation benefits
        4. Market value and demand
        5. Water availability

        For each recommended crop, provide:
        - Crop name and variety
        - Growing season (Rabi/Kharif/Zaid)
        - Expected duration
        - Water requirements
        - Expected yield per acre
        - Key benefits
        - Special considerations

        Structure the response as clear recommendations with detailed points for each crop."""
        
        response = model.generate_content(prompt)
        recommendations = response.text
        
        # Save to database
        recommendation = CropRecommendation.objects.create(
            farm=farm,
            climate_description=recommendations,  # Store the complete recommendations here
            soil_description=f"{farm.soil_type} soil characteristics",
            previous_crop_impact=f"Previous crop: {farm.previous_crop}",
            water_analysis="Based on local conditions"
        )
        
        messages.success(request, "Crop recommendations generated successfully!")
        return redirect('core:view_recommendations')
        
    except Exception as e:
        messages.error(request, f"Error generating recommendations: {str(e)}")
        return redirect('core:farm_details')

@login_required
def view_recommendations(request):
    try:
        farm = Farm.objects.filter(user=request.user).latest('created_at')
        recommendation = CropRecommendation.objects.filter(farm=farm).latest('created_at')
        
        # Process the stored text into sections
        context = {
            'farm': farm,
            'recommendation': recommendation,
            'climate_sections': parse_section_content(recommendation.climate_description),
            'soil_sections': parse_section_content(recommendation.soil_description),
            'previous_crop_sections': parse_section_content(recommendation.previous_crop_impact),
            'water_analysis': recommendation.water_analysis,
        }
        
        return render(request, 'core/crop_recommendation.html', context)
        
    except Farm.DoesNotExist:
        messages.warning(request, "Please add your farm details first.")
        return redirect('core:farm_details')
    except CropRecommendation.DoesNotExist:
        return render(request, 'core/crop_recommendation.html', {
            'farm': farm,
            'recommendation': None
        })

def parse_section_content(content):
    """Helper function to parse bulleted content into a structured format"""
    if not content:
        return []
    
    sections = []
    current_title = ''
    current_points = []
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('-'):
            current_points.append(line[1:].strip())
        else:
            if current_title and current_points:
                sections.append({
                    'title': current_title,
                    'points': current_points
                })
                current_points = []
            current_title = line
            
    if current_title and current_points:
        sections.append({
            'title': current_title,
            'points': current_points
        })
        
    return sections
@login_required
def farm_details(request):
    try:
        farm = Farm.objects.get(user=request.user)
        form = FarmDetailsForm(instance=farm)
    except Farm.DoesNotExist:
        form = FarmDetailsForm()

    if request.method == 'POST':
        if 'farm' in locals():
            form = FarmDetailsForm(request.POST, instance=farm)
        else:
            form = FarmDetailsForm(request.POST)

        if form.is_valid():
            farm = form.save(commit=False)
            farm.user = request.user
            farm.save()
            messages.success(request, 'Farm details saved successfully!')
            return redirect('core:view_recommendations')  # Updated this line
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'core/farm_details.html', {'form': form})

# @login_required
# def crop_recommendation(request):
#     farm = Farm.objects.filter(user=request.user).latest('created_at')
    
#     # Initialize Gemini API
#     genai.configure(api_key=config('GEMINI_API_KEY'))
#     model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
#     # Generate crop recommendation
#     prompt = f"""Based on the following farm details:
#     Location: {farm.location}
#     Total Area: {farm.total_area} acres
#     Soil Type: {farm.soil_type}
#     Previous Crop: {farm.previous_crop}
    
#     Suggest suitable crops for cultivation, considering local climate and soil conditions."""
    
#     response = model.generate_content(prompt)
#     recommendations = response.text
    
#     return render(request, 'core/crop_recommendation.html', 
#                  {'recommendations': recommendations})

def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    return render(request, 'errors/500.html', status=500)

@login_required
def monitoring_dashboard(request):
    farm = Farm.objects.get(user=request.user)
    current_plans = CropPlan.objects.filter(
        farm=farm,
        harvest_date__gte=datetime.now().date()
    )
    
    schedules = MonitoringSchedule.objects.filter(
        crop_plan__in=current_plans,
        date__gte=datetime.now().date()
    ).order_by('date')[:10]
    
    pest_alerts = PestAlert.objects.filter(
        farm=farm,
        resolved=False
    )
    
    context = {
        'schedules': schedules,
        'pest_alerts': pest_alerts,
        'current_plans': current_plans
    }
    return render(request, 'core/monitoring_dashboard.html', context)

@login_required
def complete_task(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(MonitoringSchedule, id=task_id)
        notes = request.POST.get('notes', '')
        
        task.completed = True
        task.notes = notes
        task.save()
        
        messages.success(request, 'Task marked as completed!')
        return redirect('monitoring_dashboard')

@login_required
def generate_pesticide_recommendations(request, plan_id):
    plan = get_object_or_404(CropPlan, id=plan_id, farm__user=request.user)
    
    try:
        recommendations = get_pesticide_recommendations(
            plan.crop_name,
            determine_growth_stage(plan)
        )
        
        plan.pesticides = recommendations
        plan.save()
        
        messages.success(request, "Pesticide recommendations generated successfully!")
    except Exception as e:
        messages.error(request, "Failed to generate pesticide recommendations. Please try again later.")
    
    return redirect('core:plan_detail', plan_id=plan.id)

def determine_growth_stage(plan):
    """Determine the current growth stage based on planting date"""
    days_since_planting = (timezone.now().date() - plan.planting_date).days
    
    if days_since_planting < 30:
        return "initial"
    elif days_since_planting < 60:
        return "vegetative"
    else:
        return "reproductive"