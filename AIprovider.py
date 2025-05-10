import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="HIPAA DocGen Platform", layout="wide")

# Sidebar Configuration
st.sidebar.title("🔧 Configuration")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Page Title
st.title("🏥 HIPAA-Compliant Documentation Generator")

# Step 1: Clinical Input Only
st.header("📄 Step 1: Enter Clinical Summary")
clinical_data = st.text_area(
    "Paste clinical summary (labs, imaging, vitals, HPI, PMH, etc.):", 
    height=300
)

# Step 2: Status Recommendation
st.header("🧠 Step 2: Inpatient vs. Observation Evaluation")
include_status_eval = st.checkbox("Evaluate status using InterQual-guided logic")

# Step 3: DVT Prophylaxis Recommendation
st.header("🦵 Step 3: DVT Prophylaxis")
include_dvt = st.checkbox("Recommend DVT prophylaxis based on renal function")
creatinine_value = st.number_input("Patient Creatinine (mg/dL)", min_value=0.1, max_value=15.0, step=0.1)

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

        # Prompt construction
        prompt = f"""
        You are a clinical documentation and triage AI.

        Step 1: From the clinical summary, extract the patient name (if present) and likely admitting diagnosis or chief complaint.

        Step 2: Generate a professional medical note (use H&P format unless context indicates otherwise).

        Step 3: Determine if the case qualifies for Inpatient or Observation status using InterQual-style criteria and explain.

        {"Step 4: Recommend DVT prophylaxis. Use Heparin if creatinine > 2.0, otherwise Lovenox. Creatinine: " + str(creatinine_value) + " mg/dL" if include_dvt else ""}

        {"Step 5: Identify all relevant specialties that should be consulted. For each, generate a professional consult message that begins with: 'Hello, may I please consult you on...'" if include_consult else ""}

        Clinical Summary:
        {clinical_data}

        Please format the output with clear section headers like:
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

                # Parse and display sections
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
                    elif section:
                        st.markdown(f"### {section}")

                # Download output
                st.download_button(
                    label="📥 Download Note as .txt",
                    data=output,
                    file_name="generated_note.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"❌ Error: {e}")
