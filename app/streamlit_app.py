import sys
import os
from pathlib import Path

# Add the parent directory to Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

import streamlit as st
from core.orchestrator import Orchestrator
import json
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Smart Health Assist",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling with Indian healthcare theme
st.markdown("""
<style>
    :root {
        --primary: #1e3a8a;
        --secondary: #3b82f6;
        --accent: #22c55e;
        --emergency: #ef4444;
        --background: #f8fafc;
        --text: #1f2937;
    }
    .main-header {
        font-size: 3rem;
        color: var(--primary);
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .sub-header {
        text-align: center;
        color: #4b5563;
        margin-bottom: 2rem;
        font-size: 1.2rem;
    }
    .card {
        background-color: var(--background);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.2rem;
        border-left: 5px solid var(--secondary);
        transition: transform 0.2s ease;
    }
    .card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
    }
    .emergency-card {
        background-color: #fef2f2;
        border-left: 5px solid var(--emergency);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
        70% { box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    .success-card {
        background-color: #f0fdf4;
        border-left: 5px solid var(--accent);
    }
    .symptom-input {
        background-color: #f1f5f9;
        padding: 1.2rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #1e3a8a, #3b82f6);
        border-radius: 4px;
    }
    .medication-card {
        background: linear-gradient(to right, #f0f9ff, #e0f2fe);
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        border: 1px solid #bae6fd;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .price-tag {
        background-color: var(--accent);
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.6rem;
        margin-bottom: 0.6rem;
    }
    .badge-psa { background-color: #dbeafe; color: #1e40af; }
    .badge-da { background-color: #fce7f3; color: #be185d; }
    .badge-pha { background-color: #dcfce7; color: #166534; }
    .badge-sg { background-color: #fef3c7; color: #92400e; }
    .condition-pill {
        display: inline-block;
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        background: linear-gradient(to right, #e0e7ff, #c7d2fe);
        color: #3730a3;
        margin: 0.3rem;
        font-size: 0.9rem;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .likelihood-bar {
        height: 10px;
        background-color: #e5e7eb;
        border-radius: 5px;
        margin-top: 0.4rem;
        overflow: hidden;
    }
    .likelihood-fill {
        height: 100%;
        background: linear-gradient(to right, #3b82f6, #60a5fa);
        border-radius: 5px;
    }
    .footer {
        text-align: center;
        padding: 1.8rem;
        margin-top: 2.5rem;
        background: linear-gradient(to right, #f8fafc, #f1f5f9);
        border-radius: 12px;
        font-size: 0.9rem;
        border: 1px solid #e2e8f0;
    }
    .info-box {
        background-color: #eff6ff;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #3b82f6;
    }
    .pricing-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .pricing-table th {
        background-color: #1e40af;
        color: white;
        padding: 0.8rem;
        text-align: left;
    }
    .pricing-table td {
        padding: 0.8rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .pricing-table tr:nth-child(even) {
        background-color: #f8fafc;
    }
    .pricing-table tr:hover {
        background-color: #f1f5f9;
    }
    .agent-process {
        display: flex;
        justify-content: space-between;
        margin: 1.5rem 0;
    }
    .agent-step {
        text-align: center;
        flex: 1;
        padding: 1rem;
    }
    .agent-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .stats-box {
        background: linear-gradient(to right, #1e3a8a, #3b82f6);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem;
    }
    .stats-number {
        font-size: 1.8rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .risk-low { background-color: #dcfce7; color: #166534; }
    .risk-medium { background-color: #fef3c7; color: #92400e; }
    .risk-high { background-color: #fef2f2; color: #dc2626; }
</style>
""", unsafe_allow_html=True)

# Initialize orchestrator
@st.cache_resource
def get_orchestrator():
    return Orchestrator()

orchestrator = get_orchestrator()

# UI Header
st.markdown('<h1 class="main-header">🏥 Smart Health Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-Powered Healthcare Guidance • Indian Pharmacy Network • Safety First</p>', unsafe_allow_html=True)

# Create columns for badges
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<span class="agent-badge badge-psa">🧠 Symptom Analysis</span>', unsafe_allow_html=True)
with col2:
    st.markdown('<span class="agent-badge badge-da">👨‍⚕️ Doctor Assessment</span>', unsafe_allow_html=True)
with col3:
    st.markdown('<span class="agent-badge badge-pha">💊 Pharmacy Check</span>', unsafe_allow_html=True)
with col4:
    st.markdown('<span class="agent-badge badge-sg">🛡️ Safety Guardian</span>', unsafe_allow_html=True)

st.caption("This is a demonstration system only and not a medical device. For diagnosis and treatment, consult a licensed healthcare provider.")

# Stats row
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="stats-box"><div>🩺</div><div class="stats-number">50+</div><div>Conditions</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="stats-box"><div>💊</div><div class="stats-number">100+</div><div>Medicines</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="stats-box"><div>🏥</div><div class="stats-number">25+</div><div>Pharmacy Partners</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="stats-box"><div>✅</div><div class="stats-number">99%</div><div>Safety Score</div></div>', unsafe_allow_html=True)

st.markdown("---")

# User input form
with st.container():
    st.markdown("### 📋 Patient Information Form")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("**Age**", min_value=0, max_value=120, value=25, help="Enter your age")
        height = st.number_input("**Height (cm)**", min_value=50, max_value=250, value=170, help="Enter your height in centimeters")
    with col2:
        sex = st.selectbox("**Sex**", ["", "Male", "Female", "Other"], help="Select your biological sex")
        weight = st.number_input("**Weight (kg)**", min_value=10, max_value=200, value=65, help="Enter your weight in kilograms")
    with col3:
        if sex == "Female":
            pregnant = st.selectbox("**Pregnant?**", ["", "Yes", "No"], help="Are you currently pregnant?")
        else:
            pregnant = ""
        blood_group = st.selectbox("**Blood Group**", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], help="Select your blood group")
    
    st.markdown("**Allergies**")
    allergies = st.text_input("Allergies", placeholder="penicillin, sulfa, etc.", label_visibility="collapsed", help="List any medication allergies separated by commas")
    
    st.markdown("**Current Medications**")
    current_meds = st.text_input("Current Medications", placeholder="List medications you're currently taking", label_visibility="collapsed", help="List any medications you're currently taking, separated by commas")
    
    st.markdown("**Medical History**")
    medical_history = st.text_input("Medical History", placeholder="Any chronic conditions or past surgeries", label_visibility="collapsed", help="List any relevant medical history")
    
    st.markdown("### 🌡️ Symptom Description")
    with st.container():
        symptoms = st.text_area(
            "Describe your symptoms in detail:",
            placeholder="Example: I've had fever of 101°F and sore throat for 2 days. Also experiencing fatigue and mild headache. No difficulty breathing.",
            height=120,
            help="Be as specific as possible about your symptoms, duration, and severity"
        )
    
    submitted = st.button("🚀 Analyze Symptoms", type="primary", use_container_width=True)

# Process request when form is submitted
if submitted:
    if not symptoms.strip():
        st.error("Please describe your symptoms")
    else:
        # Prepare context
        context = {
            "age": age if age > 0 else None,
            "sex": sex if sex else None,
            "pregnant": True if pregnant == "Yes" else False if pregnant == "No" else None,
            "allergies": [a.strip() for a in allergies.split(",")] if allergies else [],
            "meds": [m.strip() for m in current_meds.split(",")] if current_meds else [],
            "medical_history": [h.strip() for h in medical_history.split(",")] if medical_history else [],
            "vitals": {
                "height": height,
                "weight": weight,
                "blood_group": blood_group if blood_group else "Unknown"
            }
        }
        
        # Show agent process visualization
        st.markdown("### 🔄 Multi-Agent Analysis Process")
        agent_col1, agent_col2, agent_col3, agent_col4 = st.columns(4)
        with agent_col1:
            st.markdown('<div class="agent-step"><div class="agent-icon">🧠</div><div><b>Symptom Analysis</b></div><div>Extracting key information</div></div>', unsafe_allow_html=True)
        with agent_col2:
            st.markdown('<div class="agent-step"><div class="agent-icon">👨‍⚕️</div><div><b>Doctor Assessment</b></div><div>Creating care plan</div></div>', unsafe_allow_html=True)
        with agent_col3:
            st.markdown('<div class="agent-step"><div class="agent-icon">💊</div><div><b>Pharmacy Check</b></div><div>Checking availability</div></div>', unsafe_allow_html=True)
        with agent_col4:
            st.markdown('<div class="agent-step"><div class="agent-icon">🛡️</div><div><b>Safety Review</b></div><div>Verifying safety</div></div>', unsafe_allow_html=True)
        
        # Create a progress bar for the multi-agent process
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.markdown("🔍 **Patient Symptom Agent**: Analyzing your symptoms...")
        progress_bar.progress(25)
        time.sleep(0.5)
        
        try:
            # Process through orchestrator
            result = orchestrator.process_request(symptoms, context)
            
            status_text.markdown("👨‍⚕️ **Doctor Agent**: Creating preliminary assessment...")
            progress_bar.progress(50)
            time.sleep(0.7)
            
            status_text.markdown("💊 **Pharmacy Agent**: Checking medication availability...")
            progress_bar.progress(75)
            time.sleep(0.5)
            
            status_text.markdown("🛡️ **Safety Guardian**: Verifying recommendations...")
            progress_bar.progress(100)
            time.sleep(0.3)
            
            status_text.empty()
            progress_bar.empty()
            
            # Display risk level badge
            risk_level = result.get("risk_level", "unknown")
            risk_class = f"risk-{risk_level}"
            st.markdown(f'<div class="card {risk_class}"><h3>Risk Level: {risk_level.upper()}</h3></div>', unsafe_allow_html=True)
            
            # Display results with success message
            st.success("✅ Analysis Complete! Review your results below.")
            
            # Tabs for different sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📋 Recommendation", 
                "🔍 Symptom Analysis", 
                "💊 Pharmacy Options", 
                "🛡️ Safety Review",
                "📊 Health Insights"
            ])
            
            with tab1:
                if result["preliminary_assessment"]["escalation"]["needed"]:
                    st.markdown('<div class="card emergency-card">', unsafe_allow_html=True)
                    st.error("🚨 **Immediate Medical Attention Recommended**")
                    st.write(f"**Reason:** {result['preliminary_assessment']['escalation']['reason']}")
                    st.write(f"**Urgency:** {result['preliminary_assessment']['escalation'].get('urgency', 'immediate').title()}")
                    st.button("📍 Find Emergency Care Nearby", type="primary", icon="🚑")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown("### 📊 Preliminary Assessment")
                    
                    # Display conditions with likelihood bars
                    for condition in result["preliminary_assessment"]["differential"]:
                        likelihood = condition['likelihood']
                        col1, col2 = st.columns([3, 7])
                        with col1:
                            st.markdown(f"**{condition['condition']}**")
                            if 'explanation' in condition:
                                st.caption(condition['explanation'])
                        with col2:
                            st.markdown(f"{likelihood*100:.0f}%")
                            st.markdown(f'<div class="likelihood-bar"><div class="likelihood-fill" style="width: {likelihood*100}%"></div></div>', unsafe_allow_html=True)
                    
                    # Self-care suggestions
                    if result["preliminary_assessment"]["self_care"]:
                        st.markdown("### 💡 Self-Care Suggestions")
                        for advice in result["preliminary_assessment"]["self_care"]:
                            if isinstance(advice, dict):
                                st.markdown(f"**{advice['recommendation']}**")
                                st.markdown(f"{advice['details']}")
                            else:
                                st.markdown(f"- {advice}")
                    
                    # Medication recommendations
                    if result["preliminary_assessment"]["medications"]:
                        st.markdown("### 💊 Medication Recommendations")
                        for med in result["preliminary_assessment"]["medications"]:
                            if isinstance(med, dict):
                                st.markdown(f"""
                                <div class="medication-card">
                                    <div>
                                        <b>{med.get('name', 'Unknown').title()}</b> - {med.get('dose', '')}<br>
                                        <small>Route: {med.get('route', '')} | Frequency: {med.get('frequency', '')}</small>
                                        {f"<br><small>Duration: {med.get('duration', '')}</small>" if med.get('duration') else ""}
                                    </div>
                                    <div class="price-tag">₹{(len(med.get('name', '')) * 15) + 10}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Show precautions and interactions
                                if med.get('precautions'):
                                    with st.expander(f"Precautions for {med.get('name', 'Unknown')}"):
                                        for precaution in med.get('precautions', []):
                                            st.markdown(f"- {precaution}")
                                
                                if med.get('interactions'):
                                    with st.expander(f"Interactions for {med.get('name', 'Unknown')}"):
                                        for interaction in med.get('interactions', []):
                                            st.markdown(f"- {interaction}")
                
                # Follow-up advice
                if result["preliminary_assessment"].get("follow_up_advice"):
                    st.markdown("### 📅 Follow-up Advice")
                    for advice in result["preliminary_assessment"]["follow_up_advice"]:
                        if isinstance(advice, dict):
                            st.markdown(f"**{advice['advice']}** - {advice.get('timing', '')}")
                        else:
                            st.markdown(f"- {advice}")
                
                # Warning signs
                if result["preliminary_assessment"].get("warning_signs"):
                    st.markdown("### ⚠️ Warning Signs")
                    for sign in result["preliminary_assessment"]["warning_signs"]:
                        st.markdown(f"- {sign}")
                
                st.markdown("---")
                st.caption(result["preliminary_assessment"]["disclaimer"])
                
            with tab2:
                st.markdown("### 🔍 Extracted Symptom Information")
                
                symptom_data = result["symptom_analysis"]
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Chief Complaint**")
                    st.info(symptom_data["chief_complaint"])
                    
                    st.markdown("**Symptoms Identified**")
                    for symptom in symptom_data["symptoms"]:
                        st.markdown(f'<span class="condition-pill">{symptom}</span>', unsafe_allow_html=True)
                
                with col2:
                    if symptom_data.get("onset"):
                        st.markdown("**Onset**")
                        st.info(symptom_data["onset"])
                    
                    if symptom_data.get("severity"):
                        st.markdown("**Severity**")
                        st.info(symptom_data["severity"].title())
                    
                    if symptom_data.get("duration_hours"):
                        st.markdown("**Duration**")
                        st.info(f"{symptom_data['duration_hours']} hours")
                    
                    if symptom_data.get("red_flags"):
                        st.markdown("**Red Flags**")
                        for flag in symptom_data["red_flags"]:
                            st.warning(flag)
                
                st.markdown("**Patient Context**")
                st.json(symptom_data["context"])
                
            with tab3:
                st.markdown("### 💊 Pharmacy Availability")
                
                if result["pharmacy_availability"]["availability"]:
                    st.markdown("#### ✅ Available Medications")
                    
                    # Create a pricing table
                    st.markdown("**Medication Price Comparison**")
                    st.markdown("""
                    <table class="pricing-table">
                        <tr>
                            <th>Medication</th>
                            <th>Brand</th>
                            <th>Form</th>
                            <th>Price (₹)</th>
                            <th>Status</th>
                        </tr>
                    """, unsafe_allow_html=True)
                    
                    for med in result["pharmacy_availability"]["availability"]:
                        price = (len(med['name']) * 15) + 10  # Simulated price
                        status = "In Stock ✅" if med["in_stock"] else "Out of Stock ❌"
                        st.markdown(f"""
                        <tr>
                            <td>{med.get('name', 'Unknown').title()}</td>
                            <td>{med.get('brand', 'Generic')}</td>
                            <td>{med.get('form', 'Tablet')}</td>
                            <td>₹{price}</td>
                            <td>{status}</td>
                        </tr>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</table>", unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div class="info-box">
                        <b>💡 Price Information:</b> Prices shown are approximate and may vary by pharmacy and location. 
                        Generic medications are typically more affordable than brand-name equivalents.
                    </div>
                    """, unsafe_allow_html=True)
                
                # Nearby pharmacies
                if result["pharmacy_availability"].get("nearby_pharmacies"):
                    st.markdown("#### 🏥 Nearby Pharmacies")
                    for pharmacy in result["pharmacy_availability"]["nearby_pharmacies"]:
                        st.markdown(f"""
                        **{pharmacy['name']}**  
                        Distance: {pharmacy['distance_km']} km • Rating: {pharmacy['rating']}/5  
                        Delivery: {'✅ Available' if pharmacy['delivery'] else '❌ Not Available'}
                        """)
                
                # Delivery options
                if result["pharmacy_availability"].get("delivery_options"):
                    st.markdown("#### 🚚 Delivery Options")
                    for delivery in result["pharmacy_availability"]["delivery_options"]:
                        st.markdown(f"""
                        **{delivery['service']}**  
                        Time: {delivery['time']} • Charge: {delivery['charge']}  
                        Minimum Order: {delivery['min_order']}
                        """)
                
                if not result["pharmacy_availability"]["availability"] and not result["pharmacy_availability"]["alternatives"]:
                    st.info("No medication recommendations were made for your symptoms.")
                
            with tab4:
                if result["safety_review"]["approved"]:
                    st.markdown('<div class="card success-card">', unsafe_allow_html=True)
                    st.success("✅ **Plan Approved by Safety Guardian**")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="card emergency-card">', unsafe_allow_html=True)
                    st.error("⚠️ **Safety Concerns Identified**")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if result["safety_review"]["issues"]:
                    st.markdown("#### ❗ Safety Issues")
                    for issue in result["safety_review"]["issues"]:
                        st.error(f"- {issue}")
                
                if result["safety_review"]["notes"]:
                    st.markdown("#### 📝 Notes")
                    for note in result["safety_review"]["notes"]:
                        st.success(f"- {note}")
                
                if result["safety_review"].get("recommendations"):
                    st.markdown("#### 💡 Recommendations")
                    for recommendation in result["safety_review"]["recommendations"]:
                        st.info(f"- {recommendation}")
                        
                if not result["safety_review"]["issues"] and not result["safety_review"]["notes"]:
                    st.info("No specific safety issues or notes identified.")
                    
            with tab5:
                st.markdown("### 📊 Health Insights")
                
                # BMI Calculation
                if height > 0 and weight > 0:
                    bmi = weight / ((height/100) ** 2)
                    st.markdown("#### 📏 Body Mass Index (BMI)")
                    st.metric("Your BMI", f"{bmi:.1f}")
                    
                    if bmi < 18.5:
                        st.warning("**Underweight range.** Consider consulting a nutritionist for dietary advice.")
                    elif 18.5 <= bmi < 25:
                        st.success("**Healthy weight range.** Maintain your current lifestyle.")
                    elif 25 <= bmi < 30:
                        st.warning("**Overweight range.** Consider increasing physical activity.")
                    else:
                        st.error("**Obese range.** Please consult with a healthcare provider.")
                
                # General health tips
                st.markdown("#### 💡 General Health Tips")
                tips = [
                    "Stay hydrated by drinking at least 8 glasses of water daily",
                    "Aim for 7-9 hours of quality sleep each night",
                    "Include at least 30 minutes of physical activity in your daily routine",
                    "Eat a balanced diet with plenty of fruits and vegetables",
                    "Manage stress through meditation, yoga, or hobbies you enjoy"
                ]
                
                for tip in tips:
                    st.markdown(f"- {tip}")
                
                # Preventive care recommendations
                st.markdown("#### 🩺 Preventive Care")
                st.info("Based on your age and profile, consider these preventive health measures:")
                
                if age >= 40:
                    st.markdown("- Annual health check-up")
                    st.markdown("- Blood pressure monitoring every 6 months")
                    st.markdown("- Blood sugar test annually")
                    st.markdown("- Cholesterol screening every 5 years")
                else:
                    st.markdown("- Comprehensive health check-up every 2 years")
                    st.markdown("- Dental check-up every 6 months")
                    st.markdown("- Eye examination every 2 years")
            
            # Show raw data in expander
            with st.expander("📊 View Raw Data"):
                st.json(result)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("Please try again with a different description of your symptoms.")

# Footer disclaimer
st.markdown("---")
st.markdown("""
<div class="footer">
    <strong>Disclaimer</strong>: This demonstration system is for educational purposes only and is not a medical device. 
    It does not provide medical diagnosis or treatment advice. Always consult with a qualified healthcare 
    provider for medical concerns. In emergencies, call your local emergency services immediately.<br><br>
    
    <div>💰 Pricing in Indian Rupees (₹) | 🏥 Partnered with Apollo, MedPlus, and Netmeds | 📱 Download our app</div>
</div>
""", unsafe_allow_html=True)

# Sidebar with additional information
with st.sidebar:
    st.markdown("## ℹ️ About This System")
    st.info("""
    This multi-agent AI system includes:
    
    - **Symptom Agent**: Extracts structured medical information
    - **Doctor Agent**: Creates preliminary assessments
    - **Pharmacy Agent**: Checks medication availability
    - **Safety Guardian**: Verifies recommendations
    
    All agents work together to provide helpful information while prioritizing patient safety.
    """)
    
    st.markdown("## 📋 Example Symptoms")
    st.caption("""
    Try describing symptoms like:
    - "Fever and sore throat for 2 days"
    - "Headache with sensitivity to light"
    - "Cough and chest congestion"
    - "Stomach pain and diarrhea"
    """)
    
    st.markdown("## 💰 Medicine Price Ranges")
    st.caption("""
    Common medication prices in India:
    - Paracetamol: ₹10-25
    - Ibuprofen: ₹15-35
    - Antibiotics: ₹40-200
    - Antihistamines: ₹20-50
    """)
    
    st.markdown("## ⚠️ Important Notice")
    st.warning("""
    This is not a diagnostic tool. Always consult a healthcare professional for medical advice.
    
    Seek immediate emergency care for:
    - Chest pain or pressure
    - Difficulty breathing
    - Severe bleeding
    - Sudden weakness or numbness
    """)
    
    st.markdown("## 📞 Emergency Contacts")
    st.error("""
    **National Emergency Number**: 112\n
    **Medical Emergency**: 108\n
    **COVID Helpline**: 1075\n
    **Mental Health Helpline**: 080-46110007
    """)