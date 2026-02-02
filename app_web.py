import streamlit as st
import json
import os
import random
from datetime import datetime

# 1. 페이지 기본 설정 및 디자인
st.set_page_config(page_title="역삼 정반식당 오늘의 메뉴", page_icon="🍱", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .comment-box { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .comment-user { font-weight: bold; color: #495057; font-size: 0.9em; }
    .comment-text { margin-top: 5px; color: #212529; }
    .plus-box { background-color: #fff9db; padding: 12px; border-left: 5px solid #fab005; border-radius: 5px; margin: 15px 0; font-size: 0.95em; }
    .delete-btn { color: #ff6b6b; font-size: 0.8em; cursor: pointer; text-decoration: none; }
    </style>
    """, unsafe_allow_html=True)

# 2. 랜덤 닉네임 생성을 위한 리스트 (조합 시 100가지 이상)
ADJECTIVES = ["배고픈", "배부른", "행복한", "졸린", "열정적인", "차분한", "역삼동", "데이터", "스마트한", "깔끔한"]
NICKNAMES = ["뱀띠", "엔지니어", "미식가", "동료", "리뷰어", "점심요정", "직장인", "대리님", "과장님", "막내"]

# 3. 데이터 로드 및 저장 함수
def load_data():
    if os.path.exists("weekly_menu.json"):
        with open("weekly_menu.json", "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_data(data):
    with open("weekly_menu.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 메인 로직 시작
data = load_data()

st.title("🍱 역삼 정반식당 주간 식단표")
st.caption("Gemini AI가 분석한 최신 정보이며, 실제와 다를 수 있습니다.")
st.markdown("---")

if data:
    menu_list = data.get("주간_식단표") or data.get("주간식단표") or []
    
    if menu_list:
        day_names = [day.get("요일") for day in menu_list]
        # 오늘 요일을 기본값으로 선택 (없으면 첫 번째 요일)
        today_idx = datetime.now().weekday()
        default_idx = today_idx if today_idx < len(day_names) else 0
        
        selected_day_name = st.selectbox("📅 확인할 요일을 선택하세요", day_names, index=default_idx)
        
        # 선택된 요일의 데이터 추출
        day_content = next(item for item in menu_list if item["요일"] == selected_day_name)
        menu = day_content.get("식단", {})

        # 식단 표시 섹션
        st.info(f"### 🏠 {selected_day_name} 추천 점심")
        main_lunch = menu.get("마음까지_든_한_점심") or []
        for dish in main_lunch:
            st.write(f"👉 **{dish}**")
        
        plus_menu = menu.get("PLUS", [])
        if plus_menu:
            st.markdown(f'<div class="plus-box"><strong>➕ 오늘의 플러스 반찬:</strong> {", ".join(plus_menu)}</div>', unsafe_allow_html=True)
        
        st.divider()

        # 4. 익명 댓글 및 관리 기능
        st.subheader("💬 오늘 밥 어때요? (익명 후기)")
        
        if "comments" not in day_content:
            day_content["comments"] = []

        # 댓글 입력 폼
        with st.form(key="comment_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                new_comment = st.text_input("익명으로 자유롭게 남겨주세요", placeholder="오늘 제육볶음 양이 엄청 많아요!")
            with col2:
                submit_button = st.form_submit_button(label="등록")

        if submit_button and new_comment:
            # 30가지 이상의 조합으로 랜덤 닉네임 생성
            random_user = f"{random.choice(ADJECTIVES)} {random.choice(NICKNAMES)}_{random.randint(10, 99)}"
            
            comment_entry = {
                "id": datetime.now().timestamp(), # 삭제를 위한 고유 ID
                "user": random_user,
                "text": new_comment,
                "time": datetime.now().strftime("%H:%M") # 시간만 표시하여 깔끔하게
            }
            day_content["comments"].append(comment_entry)
            save_data(data)
            st.success(f"'{random_user}'님으로 등록되었습니다!")
            st.rerun()

        # 댓글 목록 및 삭제 기능
        if day_content["comments"]:
            # 최신순으로 정렬하여 표시
            for idx, c in enumerate(reversed(day_content["comments"])):
                with st.container():
                    col_txt, col_del = st.columns([6, 1])
                    with col_txt:
                        st.markdown(f"""
                            <div class="comment-box">
                                <div class="comment-user">👤 {c['user']} <span style="font-weight:normal; font-size:0.8em; color:#999;">({c['time']})</span></div>
                                <div class="comment-text">{c['text']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # 관리자용 삭제 버튼 (종환님만 아는 비밀번호 등으로 추후 확장 가능)
                    with col_del:
                        if st.button("삭제", key=f"del_{c['id']}"):
                            # 해당 ID 삭제 로직
                            day_content["comments"] = [item for item in day_content["comments"] if item["id"] != c["id"]]
                            save_data(data)
                            st.rerun()
        else:
            st.write("아직 후기가 없습니다. 첫 번째 후기를 남겨보세요!")
    else:
        st.warning("식단표 목록이 비어 있습니다.")
else:
    st.error("데이터를 불러올 수 없습니다. weekly_menu.json 파일을 확인해주세요.")