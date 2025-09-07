import os
import google.generativeai as genai
from typing import List, Dict, Any
from core.models import DoctorPlan, Medication, SymptomPayload
import json
import re

class DoctorAgent:
    def __init__(self):
        self.gemini_available = False
        try:
            if os.getenv("GEMINI_API_KEY"):
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                self.model = genai.GenerativeModel('gemini-pro')
                self.gemini_available = True
        except:
            self.gemini_available = False
    
    def generate_plan(self, symptom_data: SymptomPayload) -> DoctorPlan:
        """Generate a comprehensive assessment and care plan"""
        if self.gemini_available:
            try:
                prompt = f"""
                You are a medical assistant providing detailed preliminary assessment. 
                Based on the following symptoms and patient context:
                
                {symptom_data.to_dict()}
                
                Provide a comprehensive structured assessment with:
                1. Differential diagnosis (list 3-4 most likely conditions with likelihood estimates and brief explanations)
                2. Suggested diagnostic tests with reasons
                3. Detailed self-care recommendations with specific instructions
                4. Medication suggestions if appropriate (with proper dosing instructions, precautions, and duration)
                5. Clear escalation criteria and when to seek immediate care
                6. Follow-up advice and monitoring instructions
                7. Warning signs that should prompt immediate medical attention
                8. A clear disclaimer that this is not a medical diagnosis
                
                Consider patient context: {symptom_data.context.to_dict()}
                
                Return ONLY valid JSON with this structure:
                {{
                    "differential": [
                        {{
                            "condition": "condition_name", 
                            "likelihood": 0.XX,
                            "explanation": "brief reasoning"
                        }}
                    ],
                    "tests_suggested": [
                        {{
                            "test": "test_name",
                            "reason": "why this test is suggested"
                        }}
                    ],
                    "self_care": [
                        {{
                            "recommendation": "specific advice",
                            "details": "detailed instructions"
                        }}
                    ],
                    "medications": [
                        {{
                            "name": "medication_name",
                            "dose": "dose_info",
                            "route": "oral/topical/etc",
                            "frequency": "frequency_info",
                            "max_daily": "max_daily_dose",
                            "duration": "recommended_duration",
                            "precautions": ["precaution1", "precaution2"],
                            "interactions": ["interaction1", "interaction2"]
                        }}
                    ],
                    "escalation": {{
                        "needed": true/false, 
                        "reason": "reason_if_needed",
                        "urgency": "immediate/within_hours/within_days"
                    }},
                    "follow_up_advice": [
                        {{
                            "advice": "specific follow-up instruction",
                            "timing": "when to do this"
                        }}
                    ],
                    "warning_signs": ["warning1", "warning2"],
                    "disclaimer": "appropriate disclaimer text"
                }}
                """
                
                response = self.model.generate_content(prompt)
                json_str = self._extract_json(response.text)
                plan_data = json.loads(json_str)
                
                # Convert medications to Medication objects
                medications = []
                for med in plan_data.get("medications", []):
                    medications.append(Medication(**med))
                
                return DoctorPlan(
                    differential=plan_data.get("differential", []),
                    tests_suggested=plan_data.get("tests_suggested", []),
                    self_care=plan_data.get("self_care", []),
                    medications=medications,
                    escalation=plan_data.get("escalation", {"needed": False, "reason": None}),
                    disclaimer=plan_data.get("disclaimer", "Informational only; see a clinician for diagnosis."),
                    follow_up_advice=plan_data.get("follow_up_advice", []),
                    warning_signs=plan_data.get("warning_signs", [])
                )
            except Exception as e:
                print(f"Error generating doctor plan with Gemini: {e}")
        
        # Fallback plan if Gemini fails
        return self._generate_fallback_plan(symptom_data)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON string from response"""
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return text
    
    def _generate_fallback_plan(self, symptom_data: SymptomPayload) -> DoctorPlan:
        """Generate a comprehensive fallback plan"""
        symptoms = [s.lower() for s in symptom_data.symptoms]
        red_flags = [f.lower() for f in symptom_data.red_flags]
        
        # Check for red flags that require escalation
        escalation_needed = any(flag in ["chest pain", "difficulty breathing", "severe pain", 
                                        "confusion", "fainting", "bleeding"] for flag in red_flags)
        
        # Enhanced differential diagnosis based on symptoms
        differential = []
        if "fever" in symptoms and "sore throat" in symptoms:
            differential = [
                {"condition": "viral pharyngitis", "likelihood": 0.6, "explanation": "Common viral infection causing throat inflammation"},
                {"condition": "streptococcal pharyngitis", "likelihood": 0.3, "explanation": "Bacterial infection requiring antibiotic treatment"},
                {"condition": "mononucleosis", "likelihood": 0.1, "explanation": "Viral infection common in young adults"}
            ]
        elif "cough" in symptoms and "fever" in symptoms:
            differential = [
                {"condition": "viral upper respiratory infection", "likelihood": 0.7, "explanation": "Common cold or flu-like illness"},
                {"condition": "influenza", "likelihood": 0.2, "explanation": "Seasonal flu virus"},
                {"condition": "bronchitis", "likelihood": 0.1, "explanation": "Inflammation of bronchial tubes"}
            ]
        elif "headache" in symptoms:
            differential = [
                {"condition": "tension headache", "likelihood": 0.6, "explanation": "Common stress-related headache"},
                {"condition": "migraine", "likelihood": 0.3, "explanation": "Neurological condition with severe headache"},
                {"condition": "sinus headache", "likelihood": 0.1, "explanation": "Related to sinus congestion or infection"}
            ]
        elif "abdominal pain" in symptoms or "stomach pain" in symptoms:
            differential = [
                {"condition": "gastroenteritis", "likelihood": 0.5, "explanation": "Stomach flu or food-related illness"},
                {"condition": "irritable bowel syndrome", "likelihood": 0.3, "explanation": "Chronic digestive condition"},
                {"condition": "acid reflux", "likelihood": 0.2, "explanation": "Stomach acid flowing back into esophagus"}
            ]
        else:
            differential = [
                {"condition": "general symptoms requiring evaluation", "likelihood": 1.0, "explanation": "Needs professional assessment for accurate diagnosis"}
            ]
        
        # Medication suggestions
        medications = []
        if "fever" in symptoms or "pain" in ' '.join(symptoms):
            medications.append(Medication(
                name="paracetamol",
                dose="500 mg",
                route="oral",
                frequency="every 6-8 hours as needed",
                max_daily="3000 mg",
                duration="3-5 days as needed",
                precautions=["Do not exceed maximum daily dose", "Avoid alcohol"],
                interactions=["Warfarin", "Other products containing acetaminophen"]
            ))
        
        if "cough" in symptoms:
            medications.append(Medication(
                name="dextromethorphan",
                dose="15 mg",
                route="oral",
                frequency="every 6-8 hours as needed",
                max_daily="60 mg",
                duration="7 days maximum",
                precautions=["Do not use with MAO inhibitors", "May cause drowsiness"],
                interactions=["SSRIs", "MAO inhibitors"]
            ))
        
        # Enhanced self-care recommendations
        self_care = []
        if "fever" in symptoms:
            self_care.append({
                "recommendation": "Hydration",
                "details": "Drink plenty of fluids like water, broth, or electrolyte solutions to prevent dehydration"
            })
            self_care.append({
                "recommendation": "Rest",
                "details": "Get adequate rest to help your body fight the infection"
            })
        
        if "sore throat" in symptoms:
            self_care.append({
                "recommendation": "Salt water gargle",
                "details": "Gargle with warm salt water (1/2 teaspoon salt in 1 cup water) several times daily"
            })
            self_care.append({
                "recommendation": "Throat lozenges",
                "details": "Use soothing throat lozenges or hard candy to keep throat moist"
            })
        
        # Follow-up advice
        follow_up_advice = [
            {
                "advice": "Monitor symptoms",
                "timing": "Daily until resolved"
            },
            {
                "advice": "Seek medical attention if symptoms worsen",
                "timing": "Immediately if severe symptoms develop"
            }
        ]
        
        # Warning signs
        warning_signs = [
            "Difficulty breathing or shortness of breath",
            "Severe pain that doesn't improve with medication",
            "High fever (over 103°F or 39.4°C)",
            "Confusion or disorientation",
            "Persistent vomiting preventing fluid intake"
        ]
        
        return DoctorPlan(
            differential=differential,
            tests_suggested=[],
            self_care=self_care,
            medications=medications,
            escalation={
                "needed": escalation_needed, 
                "reason": "Red flag symptoms present" if escalation_needed else None,
                "urgency": "immediate" if escalation_needed else "within_days"
            },
            disclaimer="Informational only; see a clinician for proper diagnosis and treatment. This is an automated assessment and should not replace professional medical advice.",
            follow_up_advice=follow_up_advice,
            warning_signs=warning_signs
        )