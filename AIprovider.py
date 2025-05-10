import streamlit as st
import openai

st.set_page_config(page_title="HIPAA DocGen Platform", layout="wide")

# Sidebar Configuration
st.sidebar.title("🔧 Configuration")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
model_choice = st.sidebar.selectbox("OpenAI Model", ["gpt-4", "gpt-3.5-turbo"])

# Page Title
st.title("🏥 HIPAA-Compliant Documentation Generator")

# Step 1: Note Generation
st.header("📄 Step 1: Generate Medical Note")
note_type = st.selectbox("Note Type", ["H&P", "Progress Note", "Discharge Summary"])
patient_name = st.text_input("Patient Name")
admitting_diagnosis = st.text_input("Admitting Diagnosis / Chief Complaint")
clinical_data = st.text_area("Clinical Summary (labs, vitals, imaging, PMH, ROS, etc.)", height=250)

# Step 2: Status Recommendation
st.header("🧠 Step 2: Inpatient vs. Observation Evaluation")
include_status_eval = st.checkbox("Evaluate status (InterQual-guided logic)")

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
    elif not clinical_data or not admitting_diagnosis:
        st.warning("⚠️ Please fill in required clinical fields.")
    else:
        openai.api_key = api_key

        # Build prompt
        prompt = f"""
        You are an AI assistant for hospital documentation and consult communication.

        Task 1: Generate a professional {note_type} note:
        - Patient Name: {patient_name}
        - Admitting Diagnosis: {admitting_diagnosis}
        - Clinical Summary: {clinical_data}

        Task 2: Determine if the patient meets criteria for Inpatient or Observation status based on InterQual logic.
        Provide a clinical justification.

        {"Task 3: Recommend DVT prophylaxis. Use Heparin if creatinine > 2.0, otherwise Lovenox.\nCreatinine: " + str(creatinine_value) + " mg/dL" if include_dvt else ""}

        {"Task 4: Generate a consult request message to the " + consult_service + " service.\nStart with 'Hello, may I please consult you on...'\nReason for Consult: " + consult_reason if include_consult else ""}

        Format response clearly with headers for each section.
        """

        try:
            with st.spinner("⏳ Generating output..."):
                response = openai.ChatCompletion.create(
                    model=model_choice,
                    messages=[
                        {"role": "system", "content": "You are a professional hospitalist and documentation expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,
                )
                output = response.choices[0].message.content
                st.success("✅ Generated successfully!")

                # Display all content
                st.markdown(output)

                # Display consult message if included
                if include_consult and "Hello, may I please consult you on" in output:
                    consult_start = output.find("Hello, may I please consult you on")
                    consult_text = output[consult_start:]
                    st.markdown("### 📞 Consult Message")
                    st.code(consult_text.strip(), language="text")

                # Download note
                st.download_button(
                    label="📥 Download Note as .txt",
                    data=output,
                    file_name=f"{patient_name.replace(' ', '_')}_{note_type.replace(' ', '_')}.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"❌ Error: {e}")
