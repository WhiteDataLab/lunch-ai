import time
import os
import requests
import base64
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. 설정
API_KEY = os.getenv("GEMINI_API_KEY")
# Gemini 2.5 Flash 모델 경로 적용
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
TARGET_URL = "https://map.naver.com/p/entry/place/1671594903?c=15.00,0,0,0,dh&placePath=/feed"

def get_optimized_menu_url():
    """네이버 지도에서 메뉴판 URL을 추출하고 사이즈를 750x452로 최적화합니다."""
    options = Options()
    options.add_argument("--headless") # 작동 확인 후 주석 해제하여 사용하세요
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 20)
        
        # iframe 전환 (네이버 지도의 필수 단계)
        entry_iframe = wait.until(EC.presence_of_element_located((By.ID, "entryIframe")))
        driver.switch_to.frame(entry_iframe)
        
        # 이미지 로딩을 위해 하단으로 스크롤
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(3)
        
        # 자바스크립트로 큰 본문 이미지만 필터링하여 추출
        menu_url = driver.execute_script("""
            let imgs = document.querySelectorAll('img');
            for (let img of imgs) {
                // 프로필 사진을 제외하기 위해 가로 300px 이상 필터링
                if (img.width > 300 && (img.src.includes('pstatic.net') || img.src.includes('phinf.naver.net'))) {
                    return img.src;
                }
            }
            return null;
        """)
        
        if menu_url:
            # 금요일 메뉴가 잘리지 않도록 종환님이 발견한 최적 사이즈(750x452)로 교정
            optimized_url = menu_url.replace("size=678x452", "size=750x452")
            return optimized_url
        return None
    finally:
        driver.quit()

def analyze_with_gemini(img_url):
    """최적화된 이미지 URL을 제미나이에게 보내 JSON으로 변환합니다."""
    print(f"🤖 제미나이 2.5 Flash가 분석 중입니다...")
    
    # 이미지 다운로드 및 Base64 인코딩
    response = requests.get(img_url)
    img_data = base64.b64encode(response.content).decode('utf-8')
    
    payload = {
        "contents": [{
            "parts": [
                {
                    "text": (
                        "이 이미지에서 식당 이름과 월요일부터 금요일까지의 식단표를 추출해줘. "
                        "반드시 아래의 JSON 형식을 지켜서 답변해주고, 다른 설명은 하지 마.\n"
                        "{\n"
                        "  \"식당_이름\": \"...\",\n"
                        "  \"주간_식단표\": [\n"
                        "    { \"요일\": \"월요일\", \"식단\": { \"마음까지_든_한_점심\": [...], \"PLUS\": [...], \"프레쉬_박스\": [...], \"헬시맘_박스\": [...] } },\n"
                        "    ... 금요일까지 동일 구조 ...\n"
                        "  ]\n"
                        "}"
                    )
                },
                {"inline_data": {"mime_type": "image/jpeg", "data": img_data}}
            ]
        }]
    }
    
    res = requests.post(GEMINI_URL, json=payload)
    if res.status_code == 200:
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return None

if __name__ == "__main__":
    print("🍱 LUNCH-AI 수집 및 분석 파이프라인 가동")
    
    # 1단계: 최적화된 URL 확보
    final_url = get_optimized_menu_url()
    
    if final_url:
        print(f"✅ 최적화 URL 확보: {final_url}")
        
        # 2단계: 제미나이 분석
        time.sleep(2) # API 과부하 방지
        raw_result = analyze_with_gemini(final_url)
        
        if raw_result:
            # 3단계: JSON 정제 (마크다운 태그 제거)
            clean_json_str = raw_result.replace("```json", "").replace("```", "").strip()
            
            try:
                # 4단계: JSON 유효성 검증 및 파일 저장
                json_data = json.loads(clean_json_str)
                with open("weekly_menu.json", "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                print("\n✨ weekly_menu.json 파일이 성공적으로 생성되었습니다!")
            except Exception as e:
                print(f"❌ JSON 파싱 오류: {e}")
                print(f"원본 결과: {raw_result}")
    else:
        print("❌ 메뉴판 이미지를 찾지 못했습니다.")