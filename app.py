import streamlit as st
import time
import json
import os
import pandas as pd
from streamlit_sortables import sort_items
import google.generativeai as genai

# ==========================================
# CONFIGURATION (ใช้ Secrets บน Streamlit Cloud)
# ==========================================
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

st.set_page_config(page_title="PCM Biology Exam (Round 2)", layout="wide")

# Initialize AI
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
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
                st.markdown("**3.1** จงอธิบายกลไกการออกฤทธิ์ของ Atropine ในระดับโมเลกุล โดยใช้คำสำคัญ: 'Competitive Inhibition' และอธิบายว่าทำไมยานี้จึงช่วยลดอาการน้ำลายฟูมปากได้")
                essay1 = st.text_area("คำตอบ 3.1:", height=100, key="s1_essay1")
                st.markdown("**3.2** ทำไม Atropine ถึง *ไม่ช่วย* แก้อาการกล้ามเนื้อกระตุก (Muscle Fasciculation) ที่เห็นใน VDO 1?")
                essay2 = st.text_area("คำตอบ 3.2:", height=100, key="s1_essay2")
                st.session_state.answers.update({'s1_essay1': essay1, 's1_essay2': essay2})

        # ========================
        # SCENARIO 2
        # ========================
        elif sc == 2:
            if ph == 1:
                st.subheader("Scenario 2: เด็กวัยรุ่นชาย อายุ 17 ปี หมดสติ หายใจหอบลึก...")
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
                st.markdown("**3.1** จากผลตรวจร่างกายที่พบว่าผู้ป่วย 'หายใจหอบลึก' (Kussmaul breathing) จงอธิบายว่าการหายใจแบบนี้ช่วยปรับสมดุล pH ในเลือดได้อย่างไร?")
                e1 = st.text_area("คำตอบ 3.1:", height=80, key="s2_essay1")
                st.markdown("**3.2** แพทย์ให้การรักษาโดยการฉีด Insulin... พบว่าผู้ป่วยมีภาวะโพแทสเซียมต่ำ (Hypokalemia) จงอธิบายสาเหตุว่าทำไมระดับโพแทสเซียม (K⁺) ในเลือดจึงลดต่ำลงหลังได้รับอินซูลิน?")
                e2 = st.text_area("คำตอบ 3.2:", height=80, key="s2_essay2")
                st.session_state.answers.update({'s2_essay1': e1, 's2_essay2': e2})

        # ========================
        # SCENARIO 3
        # ========================
        elif sc == 3:
            if ph == 1:
                st.subheader("Scenario 3: เด็กชายอายุ 8 ปี มีอาการซีด เรื้อรัง ตัวเหลือง ตับและม้ามโต")
                diag = st.text_input("1. Diagnosis: ผู้ป่วยรายนี้เป็นโรคอะไร?", key="s3_diag")
                inherit = st.radio("2. Inheritance Pattern: โรคนี้มีลักษณะการถ่ายทอดทางพันธุกรรมแบบใด?",
                                   ["Autosomal dominant", "Autosomal recessive", "X-linked"], key="s3_inherit")
                chance = st.text_input("3. Chance: หากพ่อแม่คู่นี้ต้องการมีลูกคนต่อไป โอกาสที่ลูกจะเป็นโรค (%)", key="s3_chance")
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
                st.markdown("**3.1** ผู้ป่วยโรคนี้มักมีภาวะ 'เหล็กเกิน' (Iron Overload) แม้ไม่ได้รับประทานธาตุเหล็กเพิ่ม จงอธิบายสาเหตุ โดยเชื่อมโยงกับเรื่องการทำลายเม็ดเลือดแดง")
                e1 = st.text_area("คำตอบ 3.1:", height=80, key="s3_essay1")
                st.markdown("**3.2** ปัจจุบันมีการรักษาด้วยเทคโนโลยี CRISPR-Cas9 จงอธิบายหลักการทำงานของเทคโนโลยีนี้ในการรักษาโรคธาลัสซีเมียที่ระดับ Stem Cell ของผู้ป่วย")
                e2 = st.text_area("คำตอบ 3.2:", height=80, key="s3_essay2")
                st.session_state.answers.update({'s3_essay1': e1, 's3_essay2': e2})

        # ========================
        # SCENARIO 4
        # ========================
        elif sc == 4:
            if ph == 1:
                st.subheader("Scenario 4: ชายชาวประมง ประสบเหตุเรืออับปาง ดื่มน้ำทะเล 2 วัน")
                q1 = st.text_input("1. อาการหัวใจเต้นเร็ว ปลายมือเท้าขาวซีดเย็น เกิดจากการตอบสนองของระบบประสาทส่วน ________ ร่วมกับฮอร์โมน ________ ซึ่งหลั่งจาก ________", key="s4_q1")
                q2 = st.text_input("2. ปัสสาวะที่มีความถ่วงจำเพาะสูง (1.040) เป็นผลจากฮอร์โมน ________ ซึ่งออกฤทธิ์ที่ ________", key="s4_q2")
                st.session_state.answers.update({'s4_q1': q1, 's4_q2': q2})

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
                st.markdown("**3.1** จงใช้หลักการ Osmosis อธิบายว่าทำไมการดื่มน้ำทะเล จึงทำให้ร่างกายขาดน้ำรุนแรงกว่าเดิม")
                e1 = st.text_area("คำตอบ 3.1:", height=80, key="s4_essay1")
                st.markdown("**3.2** ผู้ป่วยมีความดันโลหิตต่ำวิกฤต (80/50 mmHg) แพทย์ต้องการให้สารน้ำทางหลอดเลือดดำเพื่อกู้ชีพ... จงเลือกชนิดของสารน้ำที่เหมาะสมที่สุดและอธิบายเหตุผล")
                options = ["Normal saline (0.9% NaCl)", "0.45% NaCl", "5% Dextrose/Water", "Plasma", "Whole blood"]
                choice = st.selectbox("เลือกสารน้ำ:", options, key="s4_fluid_choice")
                reason = st.text_area("เหตุผล:", height=80, key="s4_reason")
                st.session_state.answers.update({'s4_choice': choice, 's4_reason': reason, 's4_essay1': e1})

        # ========================
        # SCENARIO 5
        # ========================
        elif sc == 5:
            if ph == 1:
                st.subheader("Scenario 5: นายเอ ถูกสุนัขจรจัดกัดเป็นแผลลึกหลายแผลที่ขา...")
                agents = ["Rabies Vaccine", "Rabies Immunoglobulin", "Tetanus Toxoid", "Tetanus Antitoxin"]
                types = []
                roles = []
                for agent in agents:
                    cols = st.columns(2)
                    t = cols[0].radio(f"{agent} - ประเภทภูมิคุ้มกัน", ["Active", "Passive"], key=f"s5_{agent}_type")
                    r = cols[1].radio(f"{agent} - หน้าที่หลัก", ["Immediate Neutralization", "Long-term Memory"], key=f"s5_{agent}_role")
                    types.append(t)
                    roles.append(r)
                st.session_state.answers.update({
                    's5_agents': agents,
                    's5_types': types,
                    's5_roles': roles
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
                st.markdown("**3.1** ทำไมแพทย์ต้องฉีด Rabies Immunoglobulin ให้ผู้ป่วยที่บริเวณรอบบาดแผลมากที่สุดเท่าที่จะทำได้ ในขณะที่ Rabies Vaccine ฉีดที่ต้นแขน? จงอธิบายโดยใช้หลักการกระจายตัวของเชื้อ (Viral Spread) และขนาดโมเลกุลของ Antibody")
                e1 = st.text_area("คำตอบ 3.1:", height=80, key="s5_essay1")
                st.markdown("**3.2** หากนายเอเคยได้รับวัคซีนบาดทะยักครบถ้วนเมื่อ 1 ปีก่อน แพทย์จะตัดสินใจฉีดเพียง Tetanus Toxoid 1 เข็ม โดยไม่ฉีด Tetanus Antitoxin จงอธิบายเหตุผลตามหลักการทางภูมิคุ้มกันวิทยา")
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

    # Trigger AI grading only once
    if 'ai_grading_done' not in st.session_state:
        st.session_state.ai_grading_done = True
        with st.spinner("กำลังตรวจคำตอบด้วย AI..."):
            # Scenario 1
            if 's1_essay1' in st.session_state.answers:
                g1 = get_ai_grade("Explain Atropine mechanism...", st.session_state.answers['s1_essay1'], "Muscarinic receptor, Competitive Inhibition, Antagonist, Salivary gland")
                g2 = get_ai_grade("Why doesn't Atropine help muscle fasciculation?", st.session_state.answers['s1_essay2'], "Nicotinic receptor, Skeletal muscle, Neuromuscular junction, Specificity")
                st.session_state.answers['s1_grade1'] = g1
                st.session_state.answers['s1_grade2'] = g2
            # ... (add other scenarios if needed)

    # Show results
    st.json(st.session_state.answers)

    # Download CSV
    df = pd.DataFrame([st.session_state.answers])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 ดาวน์โหลดผลสอบ (CSV)",
        data=csv,
        file_name=f"{st.session_state.answers.get('student_name', 'student')}_results.csv",
        mime="text/csv"
    )