import streamlit as st
import time
import json
import os
import pandas as pd
from streamlit_sortables import sort_items
import google.generativeai as genai
import requests

# ==========================================
# CONFIGURATION
# ==========================================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

st.set_page_config(page_title="PCM Biology Exam (Round 2)", layout="wide")

# Initialize AI
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')
else:
    model = None

def get_ai_grade(question, student_ans, rubric):
    if not GOOGLE_API_KEY or not model:
        return "Error: No API Key (Mock Score: 0/10)"
    try:
        prompt = f"""
Role: Biology Examiner.
Task: Grade this student answer strictly based on keywords.
Question: {question}
Student Answer: {student_ans}
Rubric Keywords: {rubric}
Output format: Give ONLY the score (0-10) and a short 1-sentence feedback.
Example: Score: 8/10. Correctly identified receptor but missed competitive inhibition.
"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {e}"

# FIELD_MAPPING จาก HTML จริงของคุณ
FIELD_MAPPING = {
    # Section 1: Student Info
    'student_name': 'entry.1428432169',

    # Scenario 1: Phase 1
    's1_p1_vdo1': 'entry.1697216375',  # VDO 1 (Leg)
    's1_p1_vdo2': 'entry.1874226739',  # VDO 2 (Eye)
    's1_p1_system': 'entry.2095042542',  # ระบบประสาท
    's1_p1_chem1': 'entry.696616887',   # กลุ่มสารเคมี 1
    's1_p1_chem2': 'entry.698531293',   # กลุ่มสารเคมี 2

    # Scenario 1: Phase 3 (Essays)
    's1_essay1': 'entry.1913130773',  # Atropine mechanism
    's1_essay2': 'entry.1292504947',  # Why not help muscle fasciculation

    # Scenario 2: Phase 1 (Hormones)
    's2_hormone_0': 'entry.1034834794',
    's2_change_0': 'entry.1826209674',
    's2_mech_0': 'entry.164598416',
    's2_hormone_1': 'entry.1904032084',
    's2_change_1': 'entry.1220042795',
    's2_mech_1': 'entry.287683897',
    's2_hormone_2': 'entry.1794613146',
    's2_change_2': 'entry.1471211990',
    's2_mech_2': 'entry.1516921212',

    # Scenario 2: Phase 3 (Essays)
    's2_essay1': 'entry.1177067011',  # Kussmaul breathing
    's2_essay2': 'entry.1474268199',  # Hypokalemia after insulin

    # Scenario 3: Phase 1
    's3_diagnosis': 'entry.104900991',
    's3_inheritance': 'entry.104900996',
    's3_chance': 'entry.104907871',

    # Scenario 3: Phase 3 (Essays)
    's3_essay1': 'entry.104932597',  # Iron overload
    's3_essay2': 'entry.104940377',  # CRISPR-Cas9

    # Scenario 4: Phase 1
    's4_q1_system': 'entry.104976657',  # ระบบประสาท
    's4_q1_hormone': 'entry.104983229',  # ฮอร์โมน
    's4_q1_source': 'entry.105054184',  # หลั่งจาก
    's4_q2_hormone': 'entry.105072213',  # ฮอร์โมนไต
    's4_q2_site': 'entry.105082017',    # ออกฤทธิ์ที่

    # Scenario 4: Phase 3 (Essays)
    's4_essay1': 'entry.105085109',  # Osmosis & seawater
    's4_choice': 'entry.105110463',   # IV fluid choice
    's4_reason': 'entry.105112557',   # Reason

    # Scenario 5: Phase 1
    's5_rv_type': 'entry.105114659',
    's5_rv_role': 'entry.105140345',
    's5_rig_type': 'entry.105143329',
    's5_rig_role': 'entry.105180974',
    's5_tt_type': 'entry.105255638',
    's5_tt_role': 'entry.105276227',
    's5_tat_type': 'entry.105283767',
    's5_tat_role': 'entry.105292936',

    # Scenario 5: Phase 3 (Essays)
    's5_essay1': 'entry.105293666',  # RIG at wound site
    's5_essay2': 'entry.105302093',  # No TAT if vaccinated before
}

# FORM_ID จากลิงก์ของคุณ
FORM_ID = "1f0bQaARZzavstDVNpEIcGH78evPRNBaGNdbd55do3UU"

# Initialize session state
if 'phase' not in st.session_state:
    st.session_state.phase = 'LOGIN'
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'current_scenario' not in st.session_state:
    st.session_state.current_scenario = 1
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = 1
if 'locked_phases' not in st.session_state:
    st.session_state.locked_phases = set()

PHASE_TIMES = {1: 120, 2: 240, 3: 240}

PDF_MAP = {
    2: "Medical Fact Sheet_Scenario2.pdf",
    3: "Medical Fact Sheet_Scenario3.pdf",
    4: "Medical Fact Sheet_Scenario4.pdf",
    5: "Medical Fact Sheet_Scenario5.pdf"
}

# ----------------------------------------------------
# LOGIN
# ----------------------------------------------------
if st.session_state.phase == 'LOGIN':
    st.title("🧬 PCM Biology Competition: Round 2")
    name = st.text_input("โรงเรียน / Student ID:")
    if st.button("เข้าสู่ห้องรอสอบ"):
        if name.strip():
            st.session_state.answers['student_name'] = name.strip()
            st.session_state.phase = 'WAIT'
            st.rerun()

# ----------------------------------------------------
# WAITING ROOM
# ----------------------------------------------------
elif st.session_state.phase == 'WAIT':
    st.header(f"ยินดีต้อนรับ: {st.session_state.answers.get('student_name')}")
    st.warning("⏳ กรุณารอสัญญาณเริ่มสอบ...")
    with st.expander("สำหรับผู้คุมสอบ (Proctor)"):
        pwd = st.text_input("รหัสผ่านเริ่มสอบ:", type="password")
        if st.button("Start Exam"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.current_scenario = 1
                st.session_state.current_phase = 1
                st.session_state.phase = 'RUNNING'
                st.rerun()
            else:
                st.error("รหัสผ่านผิด")
    if st.button("รีเฟรชสถานะ"):
        st.rerun()

# ----------------------------------------------------
# MAIN EXAM
# ----------------------------------------------------
elif st.session_state.phase == 'RUNNING':
    sc = st.session_state.current_scenario
    ph = st.session_state.current_phase
    current_key = (sc, ph)

    # Auto-advance when time runs out (silent)
    time_key = f"start_time_s{sc}_p{ph}"
    if time_key not in st.session_state:
        st.session_state[time_key] = time.time()
    elapsed = time.time() - st.session_state[time_key]
    remaining = PHASE_TIMES[ph] - elapsed
    if remaining <= 0 and current_key not in st.session_state.locked_phases:
        st.session_state.locked_phases.add(current_key)
        if ph == 3:
            if sc == 5:
                st.session_state.phase = 'FINISH'
            else:
                st.session_state.current_scenario += 1
                st.session_state.current_phase = 1
        else:
            st.session_state.current_phase += 1
        st.rerun()

    # Show PDF Fact Sheet (Scenarios 2-5)
    if sc in PDF_MAP:
        pdf_file = PDF_MAP[sc]
        if os.path.exists(pdf_file):
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="📄 เปิด Medical Fact Sheet",
                    data=f,
                    file_name=pdf_file,
                    mime="application/pdf"
                )

    # Prevent editing if locked
    if current_key in st.session_state.locked_phases:
        st.warning("🔒 ส่วนนี้ส่งคำตอบแล้ว ไม่สามารถแก้ไขได้")
    else:
        # ========================
        # SCENARIO 1
        # ========================
        if sc == 1:
            if ph == 1:
                st.subheader("Scenario 1: ชาวสวนถูกหามส่งโรงพยาบาลด้วยอาการน้ำลายฟูมปาก...")
                col1, col2 = st.columns(2)
                with col1:
                    st.info("VDO 1: อาการที่ขา")
                    try:
                        st.video("Question1_VDO1.mp4", loop=True, autoplay=True, muted=True)
                    except:
                        st.warning("ไม่พบไฟล์ VDO1")
                with col2:
                    st.info("VDO 2: อาการที่ตา")
                    try:
                        st.video("Question1_VDO2.mp4", loop=True, autoplay=True, muted=True)
                    except:
                        st.warning("ไม่พบไฟล์ VDO2")
                st.divider()
                st.markdown("### 1.1 จาก VDO 1 และ VDO 2 จงระบุชื่อเรียกทางการแพทย์ (Medical Term) ของอาการที่เกิดขึ้น")
                col_vdo1, col_vdo2 = st.columns(2)
                with col_vdo1:
                    ans1_1 = st.text_input("VDO 1 (Leg):", key="s1_p1_vdo1")
                with col_vdo2:
                    ans1_2 = st.text_input("VDO 2 (Eye):", key="s1_p1_vdo2")
                ans2 = st.radio("1.2 กลุ่มอาการดังกล่าว บ่งบอกถึงภาวะ Overstimulation ของระบบประสาทส่วนใด?",
                                ["Sympathetic", "Parasympathetic", "Somatic", "Central"])
                st.markdown("### 1.3 จงระบุชื่อ \"กลุ่มสารเคมี\" (Chemical Group) ที่เป็นสาเหตุที่เป็นไปได้มา 2 กลุ่ม")
                col_chem1, col_chem2 = st.columns(2)
                with col_chem1:
                    ans3_1 = st.text_input("1.", key="s1_p1_chem1")
                with col_chem2:
                    ans3_2 = st.text_input("2.", key="s1_p1_chem2")
                st.session_state.answers.update({
                    's1_p1_vdo1': ans1_1,
                    's1_p1_vdo2': ans1_2,
                    's1_p1_system': ans2,
                    's1_p1_chem1': ans3_1,
                    's1_p1_chem2': ans3_2
                })

            elif ph == 2:
                st.subheader("Scenario 1: Mechanism (Drag & Drop)")
                st.info("จงลากกล่องข้อความมาวางเรียงลำดับ...")
                blocks = [
                    'Toxin absorption through skin/inhalation',
                    'Inhibition of Acetylcholinesterase',
                    'Acetylcholine accumulation in Synaptic Cleft',
                    'Continuous stimulation of Muscarinic & Nicotinic Receptors',
                    'Blockage of Acetylcholine Receptors',
                    'Decreased production of Acetylcholine',
                    'Irreversible activation of Acetylcholinesterase',
                    'Massive release of Norepinephrine from Nerve endings',
                    'Inhibition of Voltage-gated Calcium Channels',
                    'Hyperpolarization of the Post-synaptic membrane'
                ]
                original_items = [{'header': 'ตัวเลือก', 'items': blocks}, {'header': 'คำตอบของคุณ', 'items': []}]
                sorted_items = sort_items(original_items, multi_containers=True)
                st.session_state.answers['s1_flowchart'] = sorted_items

            elif ph == 3:
                st.subheader("Scenario 1: Synthesis & Application")
                st.markdown("**3.1** จงอธิบายกลไกการออกฤทธิ์ของ Atropine...")
                essay1 = st.text_area("คำตอบ 3.1:", height=100, key="s1_essay1")
                st.markdown("**3.2** ทำไม Atropine ถึง *ไม่ช่วย* แก้อาการกล้ามเนื้อกระตุก?")
                essay2 = st.text_area("คำตอบ 3.2:", height=100, key="s1_essay2")
                st.session_state.answers.update({'s1_essay1': essay1, 's1_essay2': essay2})

        # ========================
        # SCENARIO 2
        # ========================
        elif sc == 2:
            if ph == 1:
                st.subheader("Scenario 2: เด็กวัยรุ่นชาย อายุ 17 ปี หมดสติ หายใจหอบลึก...")
                st.markdown("""
                **ประวัติ**: ปัสสาวะบ่อยและน้ำหนักลดมา 1 เดือน  
                **ผลตรวจทางห้องปฏิบัติการ**:  
                - Glucose: 450 mg/dL  
                - pH: 7.15  
                - HCO₃⁻: 12 mEq/L  
                - Ketone (Urine): Positive 4+  
                """)
                hormones = ["Insulin", "Glucagon", "Growth hormone", "Cortisol", "Catecholamine", "Aldosterone", "Vasopressin", "PTH"]
                for i in range(3):
                    cols = st.columns(3)
                    h = cols[0].selectbox(f"ฮอร์โมน {i+1}", hormones, key=f"s2_h{i}")
                    c = cols[1].radio("การเปลี่ยนแปลง", ["Increase", "Decrease"], key=f"s2_c{i}")
                    m = cols[2].text_input("ผลที่เกิดขึ้น (Mechanism Key)", key=f"s2_m{i}")
                    st.session_state.answers[f's2_hormone_{i}'] = h
                    st.session_state.answers[f's2_change_{i}'] = c
                    st.session_state.answers[f's2_mech_{i}'] = m

            elif ph == 2:
                st.subheader("Scenario 2: กลไกการเกิดเลือดเป็นกรด")
                blocks = [
                    'Absence of Insulin activity',
                    'Cells cannot uptake Glucose',
                    'Lipolysis / Fatty Acid Breakdown',
                    'Liver produces Ketone Bodies',
                    'Accumulation of Acid in Blood',
                    'Increased Protein Synthesis',
                    'Lactate fermentation (Anaerobic)',
                    'Kidney retains Bicarbonate'
                ]
                original_items = [{'header': 'ตัวเลือก', 'items': blocks}, {'header': 'คำตอบของคุณ', 'items': []}]
                sorted_items = sort_items(original_items, multi_containers=True)
                st.session_state.answers['s2_flowchart'] = sorted_items

            elif ph == 3:
                st.subheader("Scenario 2: Synthesis")
                st.markdown("**3.1** ... Kussmaul breathing ...")
                e1 = st.text_area("คำตอบ 3.1:", height=80, key="s2_essay1")
                st.markdown("**3.2** ... Hypokalemia ...")
                e2 = st.text_area("คำตอบ 3.2:", height=80, key="s2_essay2")
                st.session_state.answers.update({'s2_essay1': e1, 's2_essay2': e2})

        # ========================
        # SCENARIO 3
        # ========================
        elif sc == 3:
            if ph == 1:
                st.subheader("Scenario 3: เด็กชายอายุ 8 ปี มีอาการซีด เรื้อรัง ตัวเหลือง ตับและม้ามโต")
                st.markdown("""
                **ประวัติ**: พัฒนาการช้า  
                **ผลตรวจเลือด**:  
                - MCV: 65 fL  
                - Hb: 6.0 g/dL  
                - Hb typing: HbA2 10%, HbF 90%  
                **Blood Smear**: Microcytic, Hypochromic, Target cells
                """)
                try:
                    st.image("pedigree.jpg", caption="Pedigree Chart", use_column_width=True)
                except:
                    st.warning("⚠️ ไม่พบไฟล์ pedigree.jpg")
                st.markdown("**คำสั่ง**: จงตอบคำถามต่อไปนี้")
                diag = st.text_input("1. Diagnosis: ผู้ป่วยรายนี้เป็นโรคอะไร?", key="s3_diag")
                inherit = st.radio("2. Inheritance Pattern: ...",
                                   ["Autosomal dominant", "Autosomal recessive", "X-linked"], key="s3_inherit")
                chance = st.text_input("3. Chance: ... (%)", key="s3_chance")
                st.session_state.answers.update({
                    's3_diagnosis': diag,
                    's3_inheritance': inherit,
                    's3_chance': chance
                })

            elif ph == 2:
                st.subheader("Scenario 3: กลไกการเกิดโรคธาลัสซีเมีย")
                correct = [
                    'Genetic Mutation/Deletion',
                    'Defective Globin chain synthesis',
                    'Precipitation of excess Globin chains',
                    'RBC Membrane damage & Hemolysis',
                    'Chronic Hypoxia (Lack of oxygen)',
                    'Extramedullary Hematopoiesis (Liver/Spleen enlargement)'
                ]
                distractors = [
                    'Iron Deficiency from poor diet',
                    'Autoimmune destroys RBC',
                    'Polymerization of Hemoglobin S',
                    'Defective Heme synthesis',
                    'Bone marrow aplasia',
                    'Deficiency of G6PD enzyme'
                ]
                all_blocks = correct + distractors
                original_items = [{'header': 'ตัวเลือก', 'items': all_blocks}, {'header': 'คำตอบของคุณ', 'items': []}]
                sorted_items = sort_items(original_items, multi_containers=True)
                st.session_state.answers['s3_flowchart'] = sorted_items

            elif ph == 3:
                st.subheader("Scenario 3: Synthesis")
                st.markdown("**3.1** ... เหล็กเกิน ...")
                e1 = st.text_area("คำตอบ 3.1:", height=80, key="s3_essay1")
                st.markdown("**3.2** ... CRISPR-Cas9 ...")
                e2 = st.text_area("คำตอบ 3.2:", height=80, key="s3_essay2")
                st.session_state.answers.update({'s3_essay1': e1, 's3_essay2': e2})

        # ========================
        # SCENARIO 4
        # ========================
        elif sc == 4:
            if ph == 1:
                st.subheader("Scenario 4: ชายชาวประมง ประสบเหตุเรืออับปาง...")
                st.markdown("""
                **Vital Signs**: BP 80/50 mmHg, Pulse 110 bpm  
                **ผลตรวจร่างกาย**: ปากแห้งมาก, ปลายมือเท้าขาวซีดเย็น  
                **Urine**: Specific Gravity 1.040  
                **Blood Osmolarity**: 320 mOsm/L
                """)

                st.markdown("### 1. อาการหัวใจเต้นเร็ว... เกิดจากการตอบสนองของระบบประสาทส่วน ________ ร่วมกับฮอร์โมน ________ ซึ่งหลั่งจาก ________")

                col1, col2, col3 = st.columns(3)
                with col1:
                    q1_system = st.text_input("1.1 ระบบประสาทส่วน", key="s4_q1_system")
                with col2:
                    q1_hormone = st.text_input("1.2 ฮอร์โมน", key="s4_q1_hormone")
                with col3:
                    q1_source = st.text_input("1.3 หลั่งจาก", key="s4_q1_source")

                st.markdown("### 2. Kidney Function: ... เป็นผลจากฮอร์โมน ________ ซึ่งออกฤทธิ์ที่ ________")

                col4, col5 = st.columns(2)
                with col4:
                    q2_hormone = st.text_input("2.1 ฮอร์โมน", key="s4_q2_hormone")
                with col5:
                    q2_site = st.text_input("2.2 ออกฤทธิ์ที่", key="s4_q2_site")

                st.session_state.answers.update({
                    's4_q1_system': q1_system,
                    's4_q1_hormone': q1_hormone,
                    's4_q1_source': q1_source,
                    's4_q2_hormone': q2_hormone,
                    's4_q2_site': q2_site
                })

            elif ph == 2:
                st.subheader("Scenario 4: กลไกกู้ความดันโลหิต")
                correct = [
                    'Activation of Sympathetic Nervous System (Baroreceptor reflex)',
                    'Adrenal Medulla releases Adrenaline',
                    'Kidney secretes Renin & Angiotensin II formation',
                    'General Vasoconstriction & Increased Heart Rate',
                    'Adrenal Cortex secretes Aldosterone',
                    'Increased Na+ & Water Reabsorption at Kidney'
                ]
                distractors = [
                    'Increased Secretion of Atrial Natriuretic Peptide',
                    'Stimulation of Vagus Nerve (Parasympathetic)',
                    'Dilation of Peripheral Blood Vessels',
                    'Inhibition of ADH (Vasopressin) release',
                    'Increased Potassium Reabsorption',
                    'Increased Urine Output'
                ]
                all_blocks = correct + distractors
                original_items = [{'header': 'ตัวเลือก', 'items': all_blocks}, {'header': 'คำตอบของคุณ', 'items': []}]
                sorted_items = sort_items(original_items, multi_containers=True)
                st.session_state.answers['s4_flowchart'] = sorted_items

            elif ph == 3:
                st.subheader("Scenario 4: Synthesis")
                st.markdown("**3.1** ... ดื่มน้ำทะเล ...")
                e1 = st.text_area("คำตอบ 3.1:", height=80, key="s4_essay1")
                st.markdown("**3.2** ... เลือกสารน้ำ ...")
                options = ["Normal saline (0.9% NaCl)", "0.45% NaCl", "5% Dextrose/Water", "Plasma", "Whole blood"]
                choice = st.selectbox("เลือกสารน้ำ:", options, key="s4_fluid_choice")
                reason = st.text_area("เหตุผล:", height=80, key="s4_reason")
                st.session_state.answers.update({'s4_essay1': e1, 's4_choice': choice, 's4_reason': reason})

        # ========================
        # SCENARIO 5
        # ========================
        elif sc == 5:
            if ph == 1:
                st.subheader("Scenario 5: นายเอ ถูกสุนัขจรจัดกัด...")
                st.markdown("""
                **แพทย์สั่งจ่ายยา 4 ชนิด**:  
                1. Rabies Vaccine  
                2. Rabies Immunoglobulin  
                3. Tetanus Toxoid  
                4. Tetanus Antitoxin
                """)
                # Rabies Vaccine
                rv_type = st.radio("Rabies Vaccine - ประเภทภูมิคุ้มกัน", ["Active", "Passive"], key="rv_type")
                rv_role = st.radio("Rabies Vaccine - หน้าที่หลัก", ["Immediate Neutralization", "Long-term Memory"], key="rv_role")
                # Rabies Immunoglobulin
                rig_type = st.radio("Rabies Immunoglobulin - ประเภทภูมิคุ้มกัน", ["Active", "Passive"], key="rig_type")
                rig_role = st.radio("Rabies Immunoglobulin - หน้าที่หลัก", ["Immediate Neutralization", "Long-term Memory"], key="rig_role")
                # Tetanus Toxoid
                tt_type = st.radio("Tetanus Toxoid - ประเภทภูมิคุ้มกัน", ["Active", "Passive"], key="tt_type")
                tt_role = st.radio("Tetanus Toxoid - หน้าที่หลัก", ["Immediate Neutralization", "Long-term Memory"], key="tt_role")
                # Tetanus Antitoxin
                tat_type = st.radio("Tetanus Antitoxin - ประเภทภูมิคุ้มกัน", ["Active", "Passive"], key="tat_type")
                tat_role = st.radio("Tetanus Antitoxin - หน้าที่หลัก", ["Immediate Neutralization", "Long-term Memory"], key="tat_role")
                st.session_state.answers.update({
                    's5_rv_type': rv_type, 's5_rv_role': rv_role,
                    's5_rig_type': rig_type, 's5_rig_role': rig_role,
                    's5_tt_type': tt_type, 's5_tt_role': tt_role,
                    's5_tat_type': tat_type, 's5_tat_role': tat_role
                })

            elif ph == 2:
                st.subheader("Scenario 5: กลไกการป้องกันโรคพิษสุนัขบ้า")
                correct = [
                    'Rabies Virus enters the wound',
                    'Rabies Immunoglobulin binds and neutralizes virus at the wound site',
                    'Rabies vaccine stimulates Antigen Presenting Cells',
                    'Activation of Helper T-Cells & B-Cells',
                    'Production of specific Antibodies',
                    'Long-term protection against virus'
                ]
                distractors = [
                    'Tetanus Vaccine destroys virus immediately',
                    'Rabies Immunoglobulin creates Memory Cells',
                    'Tetanus Toxoid kills Rabies virus',
                    'Tetanus antitoxin activates Helper T-Cells & B-Cells'
                ]
                all_blocks = correct + distractors
                original_items = [{'header': 'ตัวเลือก', 'items': all_blocks}, {'header': 'คำตอบของคุณ', 'items': []}]
                sorted_items = sort_items(original_items, multi_containers=True)
                st.session_state.answers['s5_flowchart'] = sorted_items

            elif ph == 3:
                st.subheader("Scenario 5: Synthesis & Application")
                st.markdown("**3.1** ... RIG ที่แผล ...")
                e1 = st.text_area("คำตอบ 3.1:", height=80, key="s5_essay1")
                st.markdown("**3.2** ... ไม่ฉีด TAT ...")
                e2 = st.text_area("คำตอบ 3.2:", height=80, key="s5_essay2")
                st.session_state.answers.update({'s5_essay1': e1, 's5_essay2': e2})

        # --- ปุ่ม Next Session ---
        if st.button("⏭️ Next Session", key=f"next_btn_{sc}_{ph}"):
            st.session_state.locked_phases.add(current_key)
            if ph == 3:
                if sc == 5:
                    st.session_state.phase = 'FINISH'
                else:
                    st.session_state.current_scenario += 1
                    st.session_state.current_phase = 1
            else:
                st.session_state.current_phase += 1
            st.rerun()

# ----------------------------------------------------
# FINISH
# ----------------------------------------------------
elif st.session_state.phase == 'FINISH':
    st.balloons()
    st.success("✅ ส่งข้อสอบเรียบร้อย!")

    # Submit to Google Form
    def submit_to_google_form(data, form_id, field_mapping):
        url = f"https://docs.google.com/forms/d/e/{form_id}/formResponse"
        payload = {}
        for key, value in data.items():
            if key in field_mapping:
                payload[field_mapping[key]] = str(value)
        try:
            response = requests.post(url, data=payload)
            return response.status_code == 200
        except Exception as e:
            st.error(f"ส่งคำตอบล้มเหลว: {e}")
            return False

    if st.button("📤 ส่งคำตอบไปยังผู้คุมสอบ"):
        if submit_to_google_form(st.session_state.answers, FORM_ID, FIELD_MAPPING):
            st.success("✅ ส่งคำตอบเรียบร้อย!")
        else:
            st.error("❌ ส่งไม่สำเร็จ กรุณาลองใหม่")

    # Show results
    st.json(st.session_state.answers)

    # Download CSV (backup)
    df = pd.DataFrame([st.session_state.answers])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 ดาวน์โหลดผลสอบ (CSV)",
        data=csv,
        file_name=f"{st.session_state.answers.get('student_name', 'student')}_results.csv",
        mime="text/csv"
    )