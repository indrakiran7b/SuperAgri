# core/utils.py
import google.generativeai as genai
from decouple import config
from django.core.cache import cache
from django.core.exceptions import ValidationError
import json
from datetime import datetime, timedelta

def get_cached_or_generate(cache_key, generate_func, timeout=3600):
    """Generic caching function with rate limiting"""
    result = cache.get(cache_key)
    if result is None:
        rate_limit_key = f"rate_limit_{cache_key}"
        rate_limit = cache.get(rate_limit_key, 0)
        
        if rate_limit >= 10:  # Maximum 10 requests per hour
            raise ValidationError("API rate limit exceeded. Please try again later.")
            
        result = generate_func()
        cache.set(cache_key, result, timeout)
        cache.set(rate_limit_key, rate_limit + 1, 3600)  # Reset after 1 hour
    
    return result

def get_crop_recommendation(farm_data):
    """Get crop recommendations based on farm data"""
    def generate():
        genai.configure(api_key='AIzaSyDlEMABqE8e29jrqPEX6MhiPHsljw8fEy4')
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""Based on the following farm details:
        Location: {farm_data.get('location')}
        Total Area: {farm_data.get('total_area')} acres
        Soil Type: {farm_data.get('soil_type')}
        Previous Crop: {farm_data.get('previous_crop')}
        
        Suggest suitable crops for cultivation considering:
        1. Local climate and soil conditions
        2. Crop rotation benefits
        3. Market value and demand
        4. Water availability
        5. Growing season
        
        Format the response as a JSON with the following structure:
        {
            "recommended_crops": [
                {
                    "name": "crop name",
                    "confidence": "percentage",
                    "reason": "explanation"
                }
            ]
        }"""
        
        response = model.generate_content(prompt)
        return json.loads(response.text)
    
    cache_key = f"crop_rec_{farm_data.get('location')}_{farm_data.get('soil_type')}"
    return get_cached_or_generate(cache_key, generate)

def generate_crop_plan(crop_name, planting_date, soil_type):
    """Generate daily plan for crop cultivation"""
    def generate():
        genai.configure(api_key='AIzaSyDlEMABqE8e29jrqPEX6MhiPHsljw8fEy4')
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""Create a detailed day-by-day plan for cultivating {crop_name} in {soil_type} soil.
        Starting from planting date: {planting_date}
        Include:
        1. Key growth stages
        2. Irrigation schedule
        3. Fertilizer application
        4. Monitoring checkpoints
        5. Pest management
        6. Harvesting guidelines
        
        Format the response as a JSON with dates as keys and arrays of tasks as values."""
        
        response = model.generate_content(prompt)
        return json.loads(response.text)
    
    cache_key = f"crop_plan_{crop_name}_{soil_type}_{planting_date}"
    return get_cached_or_generate(cache_key, generate)

def get_default_pesticide_recommendations(crop_name, growth_stage):
    """Provide default pesticide recommendations when API fails"""
    common_pests = {
        "mango": {
            "initial": [
                {
                    "name": "Neem Oil",
                    "target": "Aphids, Mealybugs",
                    "application": "Every 7-14 days",
                    "safety_precautions": [
                        "Wear protective clothing and gloves",
                        "Apply during early morning or late evening",
                        "Avoid spraying on windy days"
                    ]
                },
                {
                    "name": "Copper Fungicide",
                    "target": "Anthracnose, Powdery Mildew",
                    "application": "Every 14 days preventively",
                    "safety_precautions": [
                        "Wear respiratory protection",
                        "Keep children and pets away during application",
                        "Wait 24 hours before entering treated area"
                    ]
                }
            ],
            "vegetative": [
                {
                    "name": "Bacillus thuringiensis (Bt)",
                    "target": "Leaf-eating caterpillars",
                    "application": "When pests are observed",
                    "safety_precautions": [
                        "Safe for beneficial insects",
                        "Can be applied up to day of harvest",
                        "Store in cool, dry place"
                    ]
                }
            ],
            "reproductive": [
                {
                    "name": "Sulfur Spray",
                    "target": "Mites, Powdery Mildew",
                    "application": "Every 14 days as needed",
                    "safety_precautions": [
                        "Do not apply during high temperatures",
                        "Wear eye protection",
                        "Keep away from water sources"
                    ]
                }
            ]
        },
        "default": {
            "initial": [
                {
                    "name": "Neem Oil (Organic)",
                    "target": "General insects and fungal diseases",
                    "application": "Weekly as needed",
                    "safety_precautions": [
                        "Wear protective equipment",
                        "Apply in early morning",
                        "Keep away from water bodies"
                    ]
                }
            ],
            "vegetative": [
                {
                    "name": "Insecticidal Soap",
                    "target": "Soft-bodied insects",
                    "application": "Every 7-10 days as needed",
                    "safety_precautions": [
                        "Test on small area first",
                        "Avoid application in hot sun",
                        "Reapply after rain"
                    ]
                }
            ],
            "reproductive": [
                {
                    "name": "Pyrethrin (Organic)",
                    "target": "Flying insects",
                    "application": "As needed when pests present",
                    "safety_precautions": [
                        "Avoid spraying beneficial insects",
                        "Apply in evening",
                        "Follow label instructions strictly"
                    ]
                }
            ]
        }
    }

    # Get crop-specific recommendations or fall back to default
    crop_recs = common_pests.get(crop_name.lower(), common_pests["default"])
    stage_recs = crop_recs.get(growth_stage, crop_recs["initial"])
    
    return {
        "recommendations": stage_recs,
        "general_guidelines": [
            "Always read and follow label instructions",
            "Maintain proper records of applications",
            "Practice Integrated Pest Management (IPM)",
            "Rotate pesticides to prevent resistance",
            "Monitor weather conditions before application"
        ],
        "emergency_contacts": [
            "Local Agricultural Extension: Contact your local office",
            "Poison Control: Your local emergency number",
            "Environmental Protection: Regional EPA office"
        ]
    }

def get_pesticide_recommendations(crop_name, growth_stage):
    """Get pesticide recommendations with fallback to defaults"""
    def generate():
        try:
            genai.configure(api_key='AIzaSyDlEMABqE8e29jrqPEX6MhiPHsljw8fEy4')
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            prompt = f"""Provide organic and chemical pesticide recommendations for {crop_name} during {growth_stage} growth stage.
            Include:
            1. Pesticide names
            2. Target pests/diseases
            3. Application frequency
            4. Safety precautions
            
            Format as a structured list."""
            
            response = model.generate_content(prompt)
            
            # Try to parse and structure the response
            try:
                # If we can't parse it as structured data, format the text response
                recommendations = []
                current_rec = {}
                
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line.startswith('Pesticide:') or line.startswith('Name:'):
                        if current_rec:
                            recommendations.append(current_rec)
                        current_rec = {'name': line.split(':', 1)[1].strip()}
                    elif line.startswith('Target:'):
                        current_rec['target'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Application:'):
                        current_rec['application'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Safety:'):
                        current_rec['safety_precautions'] = [
                            p.strip() for p in line.split(':', 1)[1].split(',')
                        ]
                
                if current_rec:
                    recommendations.append(current_rec)
                
                if recommendations:
                    return {
                        "recommendations": recommendations,
                        "general_guidelines": [
                            "Follow local regulations for pesticide use",
                            "Use protective equipment",
                            "Consider organic alternatives first",
                            "Keep detailed application records"
                        ],
                        "emergency_contacts": [
                            "Local Agricultural Extension Office",
                            "Poison Control Center"
                        ]
                    }
                
            except Exception:
                pass
            
            # If any part fails, use default recommendations
            return get_default_pesticide_recommendations(crop_name, growth_stage)
            
        except Exception as e:
            print(f"Error generating pesticide recommendations: {str(e)}")
            return get_default_pesticide_recommendations(crop_name, growth_stage)
    
    return get_cached_or_generate(
        f"pesticide_rec_{crop_name}_{growth_stage}",
        generate
    )

def calculate_growth_progress(crop_plan):
    """Calculate the growth progress percentage of the crop"""
    total_days = (crop_plan.harvest_date - crop_plan.planting_date).days
    days_passed = (datetime.now().date() - crop_plan.planting_date).days
    
    if days_passed < 0:
        return 0
    if days_passed > total_days:
        return 100
        
    return round((days_passed / total_days) * 100, 1)

def validate_crop_season(crop_name, planting_date):
    """Validate if the crop is suitable for the current season"""
    month = planting_date.month
    
    crop_seasons = {
        'rice': [6, 7, 8],  # June to August
        'wheat': [10, 11, 12],  # October to December
        'corn': [3, 4, 5],  # March to May
    }
    
    if crop_name.lower() in crop_seasons and month not in crop_seasons[crop_name.lower()]:
        raise ValidationError(
            f"{crop_name} is typically planted in months: "
            f"{', '.join(str(m) for m in crop_seasons[crop_name.lower()])}"
        )

def validate_soil_requirements(crop_name, soil_type):
    """Validate if the soil type is suitable for the crop"""
    soil_requirements = {
        'rice': ['clay', 'loam'],
        'wheat': ['loam', 'sandy loam'],
        'corn': ['loam', 'sandy loam', 'silt'],
    }
    
    if crop_name.lower() in soil_requirements and \
       soil_type.lower() not in soil_requirements[crop_name.lower()]:
        raise ValidationError(
            f"{crop_name} typically grows best in: "
            f"{', '.join(soil_requirements[crop_name.lower()])} soil"
        )

def generate_monitoring_schedule(crop_plan):
    """Generate monitoring schedule based on crop type and growth stages"""
    schedules = []
    current_date = crop_plan.planting_date
    
    # Define basic monitoring template if json file is not available
    default_template = {
        "stages": [
            {
                "name": "Initial Growth",
                "duration": 30,
                "tasks": [
                    {
                        "type": "irrigation",
                        "interval": 3,
                        "description": "Check soil moisture and irrigate {crop} seedlings if needed"
                    },
                    {
                        "type": "pest_check",
                        "interval": 7,
                        "description": "Inspect {crop} plants for common pests and diseases"
                    }
                ]
            }
        ]
    }
    
    try:
        with open('core/data/monitoring_templates.json', 'r') as f:
            templates = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        templates = {"default": default_template}
    
    crop_template = templates.get(crop_plan.crop_name.lower(), templates['default'])
    
    for stage in crop_template['stages']:
        stage_duration = stage['duration']
        for task in stage['tasks']:
            task_interval = task['interval']  # in days
            current_task_date = current_date
            
            while current_task_date <= current_date + timedelta(days=stage_duration):
                schedules.append({
                    'date': current_task_date,
                    'task_type': task['type'],
                    'description': task['description'].format(
                        crop=crop_plan.crop_name,
                        stage=stage['name']
                    )
                })
                current_task_date += timedelta(days=task_interval)
        
        current_date += timedelta(days=stage_duration)
    
    return schedules

def generate_default_plan(crop_name, planting_date, soil_type):
    """Generate a default plan when API fails"""
    return {
        "phases": [
            {
                "name": "Land Preparation",
                "duration": "7 days",
                "tasks": [
                    f"Clear the field of any debris and previous crop residue",
                    f"Test soil pH and nutrient levels",
                    f"Prepare the soil appropriate for {soil_type} soil type",
                    "Apply basic fertilizers based on soil test results",
                    "Create proper drainage channels if needed"
                ]
            },
            {
                "name": "Planting",
                "duration": "5 days",
                "tasks": [
                    f"Prepare {crop_name} seeds for planting",
                    "Mark planting rows with appropriate spacing",
                    f"Plant {crop_name} seeds at recommended depth",
                    "Apply starter fertilizer if needed",
                    "Water the planted area thoroughly"
                ]
            },
            {
                "name": "Initial Growth",
                "duration": "30 days",
                "tasks": [
                    "Monitor seedling emergence",
                    "Maintain proper soil moisture",
                    "Watch for early signs of pests or diseases",
                    "Remove weeds as they appear",
                    "Apply first round of fertilizer when appropriate"
                ]
            },
            {
                "name": "Main Growth Period",
                "duration": "40 days",
                "tasks": [
                    "Continue regular irrigation as needed",
                    "Monitor for pests and diseases",
                    "Apply fertilizers according to crop stage",
                    "Maintain field cleanliness",
                    "Support plants if necessary"
                ]
            },
            {
                "name": "Pre-Harvest",
                "duration": "8 days",
                "tasks": [
                    "Monitor crop maturity indicators",
                    "Prepare harvest equipment",
                    "Plan harvest logistics",
                    "Final field inspection",
                    "Organize labor if needed"
                ]
            }
        ],
        "irrigation_schedule": {
            "frequency": "every 3-4 days",
            "amount": "Based on soil moisture levels and weather conditions",
            "notes": [
                f"Adjust frequency based on {soil_type} soil characteristics",
                "Monitor soil moisture regularly",
                "Consider rainfall in irrigation planning",
                "Reduce frequency during cooler periods"
            ]
        },
        "fertilizer_schedule": [
            {
                "timing": "At planting",
                "type": "Starter fertilizer",
                "amount": "As per soil test recommendations"
            },
            {
                "timing": "30 days after planting",
                "type": "Growth fertilizer",
                "amount": "Based on crop development"
            },
            {
                "timing": "60 days after planting",
                "type": "Pre-harvest fertilizer",
                "amount": "Based on crop needs"
            }
        ],
        "monitoring_points": [
            "Daily visual inspection for first 10 days",
            "Weekly pest and disease monitoring",
            "Bi-weekly soil moisture checking",
            "Monthly soil fertility assessment",
            "Weather forecast monitoring"
        ]
    }

def generate_crop_plan(crop_name, planting_date, soil_type):
    """Generate daily plan for crop cultivation with improved error handling"""
    def generate():
        try:
            genai.configure(api_key='AIzaSyDlEMABqE8e29jrqPEX6MhiPHsljw8fEy4')
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            prompt = f"""Create a detailed cultivation plan for {crop_name} in {soil_type} soil.
            Starting from {planting_date}.
            
            Provide specific tasks and timelines for:
            1. Land preparation
            2. Planting process
            3. Growth monitoring
            4. Irrigation schedule
            5. Fertilizer application
            6. Pest management
            7. Harvest preparation
            
            Format the response as a clear, step-by-step plan."""
            
            try:
                response = model.generate_content(prompt)
                
                # Create a structured plan from the response
                text_content = response.text.strip()
                
                # If the API returned something useful, create a structured plan
                if len(text_content) > 50:  # Basic validation
                    phases = []
                    current_phase = None
                    current_tasks = []
                    
                    for line in text_content.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                            
                        if line.endswith(':'):  # This is a phase header
                            if current_phase:
                                phases.append({
                                    "name": current_phase,
                                    "duration": "14 days",  # Default duration
                                    "tasks": current_tasks
                                })
                            current_phase = line[:-1]
                            current_tasks = []
                        else:
                            current_tasks.append(line)
                    
                    # Add the last phase
                    if current_phase and current_tasks:
                        phases.append({
                            "name": current_phase,
                            "duration": "14 days",
                            "tasks": current_tasks
                        })
                    
                    if phases:  # If we successfully parsed some phases
                        return {
                            "phases": phases,
                            "irrigation_schedule": {
                                "frequency": "every 3-4 days",
                                "amount": "Based on soil moisture levels"
                            },
                            "fertilizer_schedule": [
                                {
                                    "timing": "At planting",
                                    "type": "Starter fertilizer",
                                    "amount": "As per soil test"
                                }
                            ]
                        }
                
                # If we couldn't parse the API response, use the default plan
                return generate_default_plan(crop_name, planting_date, soil_type)
                
            except Exception as api_error:
                print(f"API Error: {str(api_error)}")
                return generate_default_plan(crop_name, planting_date, soil_type)
                
        except Exception as e:
            print(f"General Error: {str(e)}")
            return generate_default_plan(crop_name, planting_date, soil_type)
    
    return get_cached_or_generate(
        f"crop_plan_{crop_name}_{soil_type}_{planting_date}",
        generate
    )