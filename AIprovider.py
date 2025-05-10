import streamlit as st
from openai import OpenAI
import re

st.set_page_config(page_title="HIPAA DocGen Platform", layout="wide")

# Sidebar
st.sidebar.title("🔧 Configuration")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Title
st.title("🏥 HIPAA-Compliant Documentation Generator")

# Step 1: Select Note Type and Enter Summary
st.header("📄 Step 1: Select Note Type and Enter Clinical Summary")
note_type = st.selectbox(
    "Select Note Type to Generate",
    ["H&P (SOAP)", "Progress Note (SOAP)", "Discharge Summary"]
)
clinical_data = st.text_area(
    "Paste clinical summary (labs, imaging, vitals, HPI, PMH, etc.):", 
    height=300
)

# Step 2: InterQual Status Evaluation
st.header("🧠 Step 2: Inpatient vs. Observation Evaluation")
include_status_eval = st.checkbox("Evaluate status using InterQual-guided logic")

# Step 3: DVT Prophylaxis
st.header("🦵 Step 3: DVT Prophylaxis")
include_dvt = st.checkbox("Automatically detect creatinine and recommend prophylaxis")

# Step 4: Auto Consult Detection
st.header("📞 Step 4: Auto-Detect Consults")
include_consult = st.checkbox("Automatically detect needed consults and generate messages")

# Submit
if st.button("🚀 Generate All"):
    if not api_key:
        st.warning("⚠️ Please enter your OpenAI API Key.")
    elif not clinical_data:
        st.warning("⚠️ Please enter the clinical summary.")
    else:
        client = OpenAI(api_key=api_key)

        # Note-specific formatting
        if note_type == "H&P (SOAP)":
            note_instruction = (
                "Generate a Hospitalist History and Physical using the following structure:\n\n"
                "Hospitalist History and Physical Exam\n\n"
                "Chief Complaint:\n\n"
                "HPI is provided by:\n\n"
                "History of Present Illness:\n\n"
                "Allergies\n\n"
                "Social History:\n\n"
                "Family History: reviewed and noncontributory\n\n"
                "Surgical history:\n\n"
                "Medical History:\n\n"
                "Home Medication List:\n\n"
                "Review of Systems\n\n"
                "Physical Exam\n\n"
                "Vitals & Measurements\n"
                "Weight Measured:\n"
                "BMI Measured:\n"
                "Height/Length Measured:\n\n"
                "Lab Results\n\n"
                "Diagnostic Results\n\n"
                "ASSESSMENT and PLAN\n"
                "- Provide a combined problem-oriented assessment and plan that addresses both acute and chronic medical problems.\n\n"
                "GI Prophylaxis\n\n"
                "DVT Prophylaxis\n\n"
                "Disposition\n\n"
                "Plan of care discussed and reviewed with Attending Doctor"
            )
        elif note_type == "Progress Note (SOAP)":
            note_instruction = (
                "Generate a Hospitalist Progress Note using the following structure:\n\n"
                "Hospitalist Progress Note\n\n"
                "SUBJECTIVE:\n"
                "Patient was seen and examined. Overnight events reviewed. Discussed with nursing.\n\n"
                "Objective\n\n"
                "Vitals\n\n"
                "Physical Exam\n\n"
                "Current Medications\n\n"
                "Lab Results\n\n"
                "I/O\n\n"
                "Diagnostic Tests\n\n"
                "ASSESSMENT/PLAN:\n"
                "- Provide a combined problem-oriented assessment and plan that addresses both acute and chronic medical problems.\n\n"
                "GI Prophylaxis\n\n"
                "DVT Prophylaxis\n\n"
                "Disposition\n\n"
                "Admission H&P reviewed, labs reviewed, vital signs reviewed, PO and IV medications reviewed, discussed plan of care in interprofessional collaboration meeting with case management, social work and PT/OT.\n"
                "Plan of care reviewed and discussed with Dr. _"
            )
        else:
            note_instruction = (
                "Generate a Hospitalist Discharge Summary using the following structure:\n\n"
                "Hospitalist Discharge Summary\n\n"
                "Reason for Admission\n\n"
                "History of Present Illness\n\n"
                "Hospital Course\n\n"
                "Procedures Performed\n\n"
                "Consultants\n\n"
                "Physical Exam\n\n"
                "Vital Signs\n\n"
                "Discharge Plan\n\n"
                "Discharge Disposition\n\n"
                "Follow-Up\n\n"
                "Problem List\n"
                "Resolved During Admission:\n\n"
                "Ongoing Medical Problems:\n\n"
                "Time Spent On Discharge\n"
                "[_] Less than 30 minutes\n"
                "[X] Greater than 30 minutes\n\n"
                "Plan of care discussed and Reviewed with Dr. _"
            )

        # Prompt
        prompt = f"""
        You are a hospitalist documentation and triage AI assistant.

        Step 1: From the clinical summary, extract the patient's name (if mentioned) and most likely admitting diagnosis or chief complaint.

        Step 2: {note_instruction}

        Step 3: Determine if the patient qualifies for Inpatient or Observation status using InterQual-style logic. Provide a brief justification.

        {"Step 4: Extract the patient's most recent creatinine from the clinical summary. If creatinine > 2.0, recommend Heparin. Otherwise, recommend Lovenox." if include_dvt else ""}

        {"Step 5: Identify all relevant specialties that should be consulted. For each, generate a consult message starting with: 'Hello, may I please consult you on...'" if include_consult else ""}

        Clinical Summary:
        {clinical_data}

        Format your response with these headers:
        ### Generated Note
        ### Status Recommendation
        ### DVT Prophylaxis Recommendation (if applicable)
        ### Consult Messages (if applicable)
        """

        try:
            with st.spinner("⏳ Generating..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a hospitalist documentation and triage assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,
                )
                output = response.choices[0].message.content
                st.success("✅ Output Generated")

                # Parse and display output
                sections = output.split("###")
                for section in sections:
                    section = section.strip()

                    if section.lower().startswith("consult messages") and include_consult:
                        st.markdown("### 📞 Consult Messages (Detected)")
                        consults = section.split("**")
                        for i in range(1, len(consults), 2):
                            specialty = consults[i].strip(": ")
                            message = consults[i+1].strip()
                            with st.expander(f"{specialty}"):
                                st.code(message, language="text")

                    elif section.lower().startswith("dvt prophylaxis recommendation") and include_dvt:
                        st.markdown("### 🦵 DVT Prophylaxis Recommendation")
                        dvt_bolded = re.sub(
                            r"(recommend(?:ed)?(?: using)? (Heparin|Lovenox))",
                            r"**\1**",
                            section,
                            flags=re.IGNORECASE
                        )
                        st.markdown(dvt_bolded)

                    elif section.lower().startswith("status recommendation") and include_status_eval:
                        st.markdown("### 🧠 Status Recommendation")
                        status_bolded = re.sub(
                            r"\b(Disposition:.*?)\b(Inpatient|Observation)\b",
                            r"\1 **\2**",
                            section,
                            flags=re.IGNORECASE
                        )
                        st.markdown(status_bolded)

                    elif section:
                        st.markdown(f"### {section}")

                # Download Button
                st.download_button(
                    label="📥 Download Note as .txt",
                    data=output,
                    file_name=f"{note_type.replace(' ', '_').replace('(', '').replace(')', '')}_note.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"❌ Error: {e}")
