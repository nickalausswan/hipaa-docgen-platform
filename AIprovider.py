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

# Step 4: Consult Request Generator
st.header("📞 Step 4: Consult Text Message")
include_consult = st.checkbox("Generate consult request message")
consult_service = st.text_input("Consulting Service (e.g., Cardiology, GI, ID)")
consult_reason = st.text_area("Reason for Consult", height=100)

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
        You are an AI hospital documentation assistant.

        Step 1: From the following clinical data, extract the patient's name (if present) and chief complaint or admitting diagnosis.

        Step 2: Use that information to generate a professional medical note (default to H&P style unless clinical context suggests otherwise).

        Step 3: Based on InterQual criteria, determine if the patient qualifies for Inpatient or Observation status and explain briefly.

        {"Step 4: Recommend DVT prophylaxis. Use Heparin if creatinine > 2.0, otherwise Lovenox.\nCreatinine: " + str(creatinine_value) + " mg/dL" if include_dvt else ""}

        {"Step 5: Generate a consult request message to the " + consult_service + " service. Start with 'Hello, may I please consult you on...' using the consult reason: " + consult_reason if include_consult else ""}

        Clinical Summary:
        {clinical_data}

        Please format the output with clear section headers.
        """

        try:
            with st.spinner("⏳ Generating..."):
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
                st.markdown(output)

                # Display consult message if included
                if include_consult and "Hello, may I please consult you on" in output:
                    start = output.find("Hello, may I please consult you on")
                    st.markdown("### 📞 Consult Message")
                    st.code(output[start:], language="text")

                # Download output
                st.download_button(
                    label="📥 Download Note as .txt",
                    data=output,
                    file_name="generated_note.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"❌ Error: {e}")
