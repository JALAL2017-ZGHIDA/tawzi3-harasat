import streamlit as st
import random
import pandas as pd
import os
from datetime import datetime, timedelta
import locale

# إعداد اللغة العربية للتواريخ
try:
    locale.setlocale(locale.LC_TIME, "ar_MA.utf8")
except:
    locale.setlocale(locale.LC_TIME, "ar_EG.utf8")

st.set_page_config(page_title="توزيع الأساتذة على الحراسة", page_icon="📅", layout="wide")

st.title("📅 برنامج توزيع الأساتذة على الحراسة مع التواريخ الفعلية")
st.markdown("### ⚖️ توزيع عادل + تتبع التاريخ الفعلي لكل يوم امتحان")

# ===== إدخال البيانات =====
teachers_input = st.text_area(
    "📋 أدخل أسماء الأساتذة مع مؤسساتهم (كل أستاذ في سطر: الاسم - المؤسسة)",
    placeholder="مثال:\nالأستاذ أحمد - ثانوية ابن خلدون\nالأستاذة فاطمة - ثانوية طه حسين"
)

institutions_input = st.text_area(
    "🏫 أدخل أسماء مراكز الامتحان (كل مركز في سطر):",
    placeholder="مثال:\nثانوية ابن خلدون\nثانوية طه حسين"
)

num_days = st.number_input("عدد أيام الامتحان:", min_value=1, value=2)
periods = st.multiselect("الفترات في اليوم:", ["صباح", "مساء"], default=["صباح", "مساء"])
num_rooms = st.number_input("عدد القاعات في كل مركز:", min_value=1, value=3)

# اختيار تاريخ البداية
start_date = st.date_input("📅 اختر تاريخ بداية الامتحان:", datetime.today())

# ملف حفظ التاريخ
history_file = "history_of_assignments.csv"
exam_year = datetime.today().year  # السنة الحالية

# تحميل أو إنشاء السجل
if os.path.exists(history_file):
    history_df = pd.read_csv(history_file)
else:
    history_df = pd.DataFrame(columns=["الأستاذ", "المركز", "تاريخ_التوزيع", "اليوم_الفعلي", "السنة"])

# ===== زر التوزيع =====
if st.button("🔄 توزيع الأساتذة بعدالة مع التواريخ"):
    if not teachers_input.strip() or not institutions_input.strip():
        st.warning("⚠️ من فضلك أدخل بيانات الأساتذة والمراكز أولًا.")
        st.stop()

    # معالجة بيانات الأساتذة
    teachers_raw = [line.strip() for line in teachers_input.split("\n") if line.strip()]
    invalid_lines = [t for t in teachers_raw if "-" not in t]
    if invalid_lines:
        st.error(f"⚠️ الأسطر التالية غير صحيحة:\n" + "\n".join(invalid_lines))
        st.stop()

    teachers = []
    for t in teachers_raw:
        name, school = [x.strip() for x in t.split("-", 1)]
        teachers.append({"name": name, "school": school})

    institutions = [line.strip() for line in institutions_input.split("\n") if line.strip()]

    # حساب عدد الحراسات السابقة
    history_counts = history_df["الأستاذ"].value_counts().to_dict()
    for t in teachers:
        t["previous"] = history_counts.get(t["name"], 0)

    # خلط عشوائي للحفاظ على العدالة عند التساوي
    random.shuffle(teachers)
    teachers.sort(key=lambda x: x["previous"])

    schedule = []
    used_in_day = set()  # لمنع التكرار في اليوم نفسه

    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        used_in_day.clear()

        for period in periods:
            for institution in institutions:
                available_teachers = [
                    t for t in teachers
                    if t["school"] != institution and t["name"] not in used_in_day
                ]

                if not available_teachers:
                    st.warning(f"⚠️ لا يوجد أساتذة متاحون ليوم {day+1} في مركز {institution}.")
                    continue

                # اختيار الأساتذة الأقل حراسات
                available_teachers.sort(key=lambda x: x["previous"])
                assigned = available_teachers[:num_rooms]

                used_in_day.update([t["name"] for t in assigned])

                for i, teacher in enumerate(assigned, start=1):
                    schedule.append({
                        "اليوم": f"اليوم {day+1}",
                        "التاريخ": current_date.strftime("%A %d %B %Y"),
                        "الفترة": period,
                        "المركز": institution,
                        "القاعة": f"قاعة {i}",
                        "الأستاذ المكلف": teacher["name"],
                        "مؤسسته الأصلية": teacher["school"],
                        "إجمالي الحراسات السابقة": teacher["previous"]
                    })

                    history_df = pd.concat([
                        history_df,
                        pd.DataFrame([{
                            "الأستاذ": teacher["name"],
                            "المركز": institution,
                            "تاريخ_التوزيع": f"اليوم {day+1} ({period})",
                            "اليوم_الفعلي": current_date.strftime("%Y-%m-%d"),
                            "السنة": exam_year
                        }])
                    ], ignore_index=True)

    if not schedule:
        st.error("❌ لم يتم إنشاء أي توزيع. تأكد من وجود عدد كافٍ من الأساتذة.")
    else:
        df = pd.DataFrame(schedule)
        st.success("✅ تم توزيع الأساتذة بعدالة مع التواريخ الفعلية!")

        st.dataframe(df, use_container_width=True)

        # حفظ البيانات
        history_df.to_csv(history_file, index=False)

        # تحميل ملف Excel
        excel_file = f"توزيع_الأساتذة_مع_التواريخ_{exam_year}.xlsx"
        df.to_excel(excel_file, index=False)
        with open(excel_file, "rb") as f:
            st.download_button("⬇️ تحميل الجدول Excel", data=f, file_name=excel_file)

# ===== تقرير الإحصائيات =====
st.markdown("---")
st.markdown("## 📊 تقرير الحراسات السابقة مع التواريخ")

if not history_df.empty:
    stats = history_df.groupby("الأستاذ").agg(
        عدد_المراكز=("المركز", "nunique"),
        عدد_الحراسات=("المركز", "count"),
        آخر_مركز=("المركز", lambda x: x.iloc[-1]),
        آخر_تاريخ=("اليوم_الفعلي", lambda x: x.iloc[-1])
    ).reset_index().sort_values(by="عدد_الحراسات")

    st.dataframe(stats, use_container_width=True)

    # إحصائية حسب المؤسسة
    st.markdown("### 🏫 توزيع عدد الأساتذة حسب مؤسساتهم الأصلية")
    if "مؤسسته الأصلية" in locals():
        summary = df.groupby("مؤسسته الأصلية")["الأستاذ المكلف"].count().reset_index()
        summary.columns = ["المؤسسة", "عدد الأساتذة المكلفين"]
        st.bar_chart(summary.set_index("المؤسسة"))

    stats_file = f"تقرير_الحراسات_مع_التواريخ_{exam_year}.xlsx"
    stats.to_excel(stats_file, index=False)
    with open(stats_file, "rb") as f:
        st.download_button("⬇️ تحميل تقرير الحراسات Excel", data=f, file_name=stats_file)
else:
    st.info("ℹ️ لا يوجد سجل حراسات بعد. قم بإجراء توزيع أولًا.")
