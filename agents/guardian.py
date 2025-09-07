from typing import List, Dict, Any
from core.models import SafetyReview, SymptomPayload, DoctorPlan, PharmacyAvailability
from core.rules import SafetyRules

class SafetyGuardian:
    def __init__(self):
        self.rules = SafetyRules()
    
    def review_plan(self, symptom_data: SymptomPayload, 
                   doctor_plan: DoctorPlan, 
                   pharmacy_data: PharmacyAvailability) -> SafetyReview:
        """Comprehensive review of the entire plan for safety issues"""
        issues = []
        notes = []
        recommendations = []
        
        # Determine risk level
        risk_level = self._determine_risk_level(symptom_data, doctor_plan)
        
        # 1. Check for red flags that require escalation
        if self.rules.check_red_flags(symptom_data.symptoms, symptom_data.red_flags):
            if not doctor_plan.escalation.get("needed", False):
                issues.append("Red flag symptoms detected but no escalation recommended")
                # Force escalation
                doctor_plan.escalation = {
                    "needed": True, 
                    "reason": "Red flag symptoms detected during safety review",
                    "urgency": "immediate"
                }
        
        # 2. Check medication safety
        context = symptom_data.context.to_dict() if hasattr(symptom_data.context, 'to_dict') else {}
        for medication in doctor_plan.medications:
            med_issues = self.rules.check_medication_safety(medication, context)
            issues.extend(med_issues)
            
            # Add specific recommendations for medication issues
            for issue in med_issues:
                if "dosing" in issue.lower():
                    recommendations.append("Consult doctor for appropriate dosage adjustment")
                elif "allergy" in issue.lower():
                    recommendations.append("Consider alternative medication due to allergy concerns")
        
        # 3. Check pregnancy contraindications
        pregnancy_issues = self.rules.check_pregnancy_contraindications(doctor_plan, context)
        issues.extend(pregnancy_issues)
        if pregnancy_issues:
            recommendations.append("Review all medications for pregnancy safety")
        
        # 4. Check pharmacy availability against allergies
        if context.get("allergies"):
            for item in pharmacy_data.availability:
                if self.rules.check_allergy_contraindication(item["name"], context["allergies"]):
                    issues.append(f"Available medication {item['name']} may be contraindicated due to allergies")
                    recommendations.append(f"Avoid {item['name']} due to allergy concerns")
        
        # 5. Check for drug interactions
        interaction_issues = self._check_drug_interactions(doctor_plan.medications, context.get("meds", []))
        issues.extend(interaction_issues)
        if interaction_issues:
            recommendations.append("Review potential drug interactions with current medications")
        
        # 6. Check age-appropriate recommendations
        age_issues = self._check_age_appropriateness(doctor_plan, context.get("age"))
        issues.extend(age_issues)
        if age_issues:
            recommendations.append("Verify age-appropriateness of all recommendations")
        
        # Add positive notes if no issues found
        if not issues:
            notes.append("All medications appear safe for this patient")
            notes.append("Dosages within recommended ranges")
            notes.append("No significant drug interactions identified")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("Follow up with healthcare provider if symptoms persist beyond 3 days")
            recommendations.append("Monitor for any adverse reactions to medications")
        
        # Check if plan should be approved
        approved = len(issues) == 0 and risk_level != "high"
        
        return SafetyReview(
            approved=approved,
            issues=issues,
            notes=notes,
            risk_level=risk_level,
            recommendations=recommendations
        )
    
    def _determine_risk_level(self, symptom_data: SymptomPayload, doctor_plan: DoctorPlan) -> str:
        """Determine the overall risk level of the plan"""
        if doctor_plan.escalation.get("needed", False):
            return "high"
        
        # Check symptom severity
        severity = symptom_data.severity.lower() if symptom_data.severity else "mild"
        if severity in ["severe", "critical"]:
            return "high"
        
        # Check for multiple medications
        if len(doctor_plan.medications) > 2:
            return "medium"
        
        # Check for complex conditions in differential
        complex_conditions = ["pneumonia", "meningitis", "sepsis", "myocardial", "stroke"]
        for condition in doctor_plan.differential:
            if any(complex in condition.get("condition", "").lower() for complex in complex_conditions):
                return "medium"
        
        return "low"
    
    def _check_drug_interactions(self, recommended_meds: List[Any], current_meds: List[str]) -> List[str]:
        """Check for potential drug interactions"""
        issues = []
        
        # Simple interaction check (in real implementation, use a drug interaction database)
        interaction_pairs = [
            ("warfarin", "aspirin"), ("warfarin", "ibuprofen"),
            ("ssri", "maoi"), ("digoxin", "quinine"),
            ("statins", "azole"), ("diuretic", "lithium")
        ]
        
        all_meds = [med.name.lower() for med in recommended_meds] + [med.lower() for med in current_meds]
        
        for med1, med2 in interaction_pairs:
            if med1 in all_meds and med2 in all_meds:
                issues.append(f"Potential interaction between {med1} and {med2}")
        
        return issues
    
    def _check_age_appropriateness(self, plan: DoctorPlan, age: int) -> List[str]:
        """Check if recommendations are age-appropriate"""
        issues = []
        
        if age is None:
            return issues
        
        # Check medications for age restrictions
        age_restricted_meds = {
            "aspirin": (16, "Should not be used in children due to Reye's syndrome risk"),
            "tetracycline": (8, "Can cause tooth discoloration in children"),
            "fluoroquinolones": (18, "Generally avoided in children due to effects on cartilage")
        }
        
        for medication in plan.medications:
            med_name = medication.name.lower()
            for restricted_med, (min_age, reason) in age_restricted_meds.items():
                if restricted_med in med_name and age < min_age:
                    issues.append(f"Medication {medication.name} {reason}")
        
        return issues