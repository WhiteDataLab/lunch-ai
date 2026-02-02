import streamlit as st
import json
import os
from datetime import datetime

# 페이지 기본 설정
st.set_page_config(page_title="역삼 정반식당 오늘의 메뉴", page_icon="🍱", layout="centered")

# CSS 커스텀 (댓글창 디자인 포함)
st.markdown("""
    <style>
    .comment-box { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 10px; }
    .comment-user { font-weight: bold; color: #555; font-size: 0.9em; }
    .comment-text { margin-top: 5px; color: #333; }
    .plus-box { background-color: #fff9db; padding: 10px; border-left: 5px solid #fab005; border-radius: 5px; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍱 역삼 정반식당 주간 식단표")
st.caption("Gemini 2.5 Flash AI가 분석한 최신 정보입니다.")
st.markdown("---")

# JSON 데이터 로드
if os.path.exists("weekly_menu.json"):
    with open("weekly_menu.json", "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            menu_list = data.get("주간_식단표") or data.get("주간식단표") or data
            
            if isinstance(menu_list, list):
                day_names = [day.get("요일") for day in menu_list]
                selected_day_name = st.selectbox("📅 확인할 요일을 선택하세요", day_names)
                
                day_content = next(item for item in menu_list if item["요일"] == selected_day_name)
                menu = day_content.get("식단", {})

                # 1. 식단 표시 섹션
                st.info(f"### 🏠 {selected_day_name} 추천 점심")
                main_lunch = menu.get("마음까지_든_한_점심") or []
                for dish in main_lunch:
                    st.write(f"👉 **{dish}**")
                
                plus_menu = menu.get("PLUS", [])
                if plus_menu:
                    st.markdown(f'<div class="plus-box"><strong>➕ 오늘의 플러스 반찬:</strong> {", ".join(plus_menu)}</div>', unsafe_allow_html=True)
                
                st.divider()

                # 2. 익명 댓글 섹션 (새로 추가)
                st.subheader("💬 오늘 밥 어때요? (익명 후기)")
                
                # 댓글 저장을 위한 구조 확인
                if "comments" not in day_content:
                    day_content["comments"] = []

                # 댓글 입력 폼
                with st.form(key="comment_form", clear_on_submit=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        new_comment = st.text_input("메뉴 구성이나 맛은 어떤가요? (익명)", placeholder="오늘 제육은 좀 맵네요!")
                    with col2:
                        submit_button = st.form_submit_button(label="등록")

                if submit_button and new_comment:
                    # 새 댓글 추가
                    comment_entry = {
                        "user": f"익명의 뱀띠_{datetime.now().strftime('%S')}", # 종환님 뱀띠 상징성 반영
                        "text": new_comment,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    day_content["comments"].append(comment_entry)
                    
                    # JSON 파일에 즉시 저장
                    with open("weekly_menu.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    st.success("후기가 등록되었습니다!")
                    st.rerun()

                # 댓글 목록 출력
                if day_content["comments"]:
                    for c in reversed(day_content["comments"]): # 최신순
                        st.markdown(f"""
                            <div class="comment-box">
                                <div class="comment-user">👤 {c['user']} <span style="font-weight:normal; font-size:0.8em;">({c['time']})</span></div>
                                <div class="comment-text">{c['text']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("아직 후기가 없어요. 첫 번째 후기를 남겨보세요!")

            else:
                st.error("❌ 데이터 구조를 확인해주세요.")

        except Exception as e:
            st.error(f"❌ 화면 표시 중 오류 발생: {e}")
else:
    st.error("📁 weekly_menu.json 파일이 없습니다.")