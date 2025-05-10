import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="HIPAA DocGen Platform", layout="wide")

# Sidebar Configuration
st.sidebar.title("🔧 Configuration")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
model_choice = st.sidebar.selectbox("OpenAI Model", ["gpt-4", "gpt-3.5-turbo"])

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

# Step 4: Automatic Consult Detection
st.header("📞 Step 4: Auto-Detect Necessary Consults")
include_consult = st.checkbox("Detect and generate consult messages automatically")

# Submit Button
if st.button("🚀 Generate All"):
    if not api_key:
        st.warning("⚠️ Please enter your OpenAI API Key.")
    elif not clinical_data:
        st.warning("⚠️ Please enter the clinical summary.")
    else:
        client = OpenAI(api_key=api_key)

        # Construct prompt
        prompt = f"""
        You are an AI assistant for hospital documentation and triage.

        Step 1: From the clinical text below, extract the patient's name (if mentioned) and the most likely admitting diagnosis or chief complaint.

        Step 2: Generate a professional medical note (default to H&P unless clinical context suggests otherwise).

        Step 3: Evaluate if the patient meets criteria for Inpatient or Observation status based on InterQual-style reasoning. Provide a brief justification.

        {"Step 4: Recommend DVT prophylaxis. Use Heparin if creatinine > 2.0, otherwise Lovenox.\nCreatinine: " + str(creatinine_value) + " mg/dL" if include_dvt else ""}

        {"Step 5: Based on the clinical scenario, identify all relevant medical or surgical specialties that should be consulted. For each, generate a brief consult request text message beginning with 'Hello, may I please consult you on...' Use a professional tone suitable for secure messaging." if include_consult else ""}

        Clinical Summary:
        {clinical_data}

        Please format the output using clear section headers:
        - Generated Note
        - Status Recommendation
        - DVT Prophylaxis Recommendation (if applicable)
        - Consult Messages (if applicable)
        """

        try:
            with st.spinner("⏳ Generating output..."):
                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[
                        {"role": "system", "content": "You are a hospitalist documentation and triage assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,
                )
                output = response.choices[0].message.content
                st.success("✅ Output Generated")

                # --- Show main output ---
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

                # --- Download full output ---
                st.download_button(
                    label="📥 Download Note as .txt",
                    data=output,
                    file_name="generated_note.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"❌ Error: {e}")
