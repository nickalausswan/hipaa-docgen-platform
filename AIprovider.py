import streamlit as st
from openai import OpenAI
import re

st.set_page_config(page_title="HIPAA DocGen Platform", layout="wide")

# Sidebar Configuration
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

# Step 2: Status Recommendation
st.header("🧠 Step 2: Inpatient vs. Observation Evaluation")
include_status_eval = st.checkbox("Evaluate status using InterQual-guided logic")

# Step 3: Auto DVT Prophylaxis Recommendation
st.header("🦵 Step 3: DVT Prophylaxis")
include_dvt = st.checkbox("Automatically detect creatinine and recommend prophylaxis")

# Step 4: Auto Consult Detection
st.header("📞 Step 4: Auto-Detect Consults")
include_consult = st.checkbox("Automatically detect needed consults and generate messages")

# Submit Button
if st.button("🚀 Generate All"):
    if not api_key:
        st.warning("⚠️ Please enter your OpenAI API Key.")
    elif not clinical_data:
        st.warning("⚠️ Please enter the clinical summary.")
    else:
        client = OpenAI(api_key=api_key)

        # Build prompt
        prompt = f"""
        You are a hospitalist documentation and triage AI assistant.

        Step 1: From the clinical text below, extract the patient's name (if present) and the most likely admitting diagnosis or chief complaint.

        Step 2: Generate a professional **{note_type}** for this patient. Use SOAP format for H&P and Progress Notes.

        Step 3: Determine if the case qualifies for Inpatient or Observation status using InterQual-style logic. Provide a brief justification.

        {"Step 4: Extract the patient's most recent creatinine from the clinical summary. If creatinine > 2.0, recommend Heparin. Otherwise, recommend Lovenox." if include_dvt else ""}

        {"Step 5: Identify all relevant specialties that should be consulted. For each, generate a professional consult message that begins with: 'Hello, may I please consult you on...'" if include_consult else ""}

        Clinical Summary:
        {clinical_data}

        Format your response using the following headers:
        ### Generated Note
        ### Status Recommendation
        ### DVT Prophylaxis Recommendation (if applicable)
        ### Consult Messages (if applicable)
        """

        try:
            with st.spinner("⏳ Generating output..."):
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

                    # 📞 Auto Consult Messages
                    if section.lower().startswith("consult messages") and include_consult:
                        st.markdown("### 📞 Consult Messages (Detected)")
                        consults = section.split("**")
                        for i in range(1, len(consults), 2):
                            specialty = consults[i].strip(": ")
                            message = consults[i+1].strip()
                            with st.expander(f"{specialty}"):
                                st.code(message, language="text")

                    # 🦵 DVT Recommendation (bold Heparin/Lovenox)
                    elif section.lower().startswith("dvt prophylaxis recommendation") and include_dvt:
                        st.markdown("### 🦵 DVT Prophylaxis Recommendation")
                        dvt_bolded = re.sub(
                            r"(recommend(?:ed)?(?: using)? (Heparin|Lovenox))",
                            r"**\1**",
                            section,
                            flags=re.IGNORECASE
                        )
                        st.markdown(dvt_bolded)

                    # 🧠 Status Recommendation (bold Inpatient or Observation)
                    elif section.lower().startswith("status recommendation") and include_status_eval:
                        st.markdown("### 🧠 Status Recommendation")
                        status_bolded = re.sub(
                            r"\b(Disposition:.*?)\b(Inpatient|Observation)\b",
                            r"\1 **\2**",
                            section,
                            flags=re.IGNORECASE
                        )
                        st.markdown(status_bolded)

                    # Other Sections
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
