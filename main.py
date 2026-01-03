import asyncio
import random
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# .env 파일로부터 환경 변수를 로드합니다.
load_dotenv()

# 환경 변수에서 아이디와 비밀번호를 가져옵니다.
USER_ID = os.getenv("SRT_ID")
USER_PW = os.getenv("SRT_PW")

# 예약 타겟 시간 설정
TARGET_START_TIME = "17:00"
TARGET_END_TIME = "20:00"


async def run_srt_automation():
    if not USER_ID or not USER_PW:
        print("❌ 에러: .env 파일에 SRT_ID 또는 SRT_PW가 설정되지 않았습니다.")
        return

    async with async_playwright() as p:
        # 브라우저 실행
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        try:
            # 1. 로그인 페이지 접속
            print("1. 로그인 페이지로 이동 중...")
            await page.goto("https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=TK0701000000")
            await page.wait_for_load_state("networkidle")

            # 로그인 정보 입력
            print("2. 로그인 정보 입력 중...")
            # 아이디 입력
            await page.fill(
                'xpath=/html/body/div/div[4]/div/div[2]/form/fieldset/div[1]/div[2]/div[2]/div/div[1]/div[1]/input',
                USER_ID)
            # 비밀번호 입력
            await page.fill(
                'xpath=/html/body/div/div[4]/div/div[2]/form/fieldset/div[1]/div[2]/div[2]/div/div[1]/div[2]/input',
                USER_PW)

            # 로그인 버튼 클릭
            await page.click(
                'xpath=/html/body/div/div[4]/div/div[2]/form/fieldset/div[1]/div[2]/div[2]/div/div[2]/input')

            # 로그인 후 페이지 변화 대기 (URL 변경 혹은 특정 요소 확인)
            # **주의**: 사이트 사정에 따라 메인으로 안 가고 팝업이 뜰 수 있어 3초 정도 강제 대기 후 이동합니다.
            await asyncio.sleep(3)
            print("✅ 로그인 프로세스 완료 (로그인 성공 여부를 브라우저에서 확인하세요)")

            # 3. 예매 조회 페이지 직접 이동
            print("3. 예매 조회 페이지로 이동...")
            await page.goto("https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000")
            await page.wait_for_load_state("networkidle")

            print(f"🔍 설정된 시간대: {TARGET_START_TIME} ~ {TARGET_END_TIME}")

            count = 1
            while True:
                # 4. 조회하기 버튼 클릭 (알려주신 XPath)
                print(f"[{count}회차] 조회 버튼 클릭...")
                await page.click('xpath=/html/body/div/div[4]/div/div[2]/form/fieldset/div[2]/input')

                # 결과 테이블이 로드될 때까지 대기
                try:
                    await page.wait_for_selector('#search-list tbody tr', timeout=3000)
                except:
                    print("결과를 불러오는 중이거나 데이터가 없습니다. 다시 시도합니다.")
                    await asyncio.sleep(1)
                    continue

                # 5. 모든 열차 행 탐색
                rows = await page.query_selector_all('#search-list tbody tr')

                found = False
                for row in rows:
                    time_element = await row.query_selector('td:nth-child(4) em.time')
                    if not time_element: continue

                    train_time = await time_element.inner_text()

                    # 시간 범위 내에 있는지 확인
                    if TARGET_START_TIME <= train_time <= TARGET_END_TIME:
                        # 해당 행 안에서 '예약하기' 버튼(burgundy_dark 클래스) 찾기
                        reserve_btn = await row.query_selector('a.btn_burgundy_dark')

                        if reserve_btn:
                            print(f"🎉 예약 가능 발견! 시간: {train_time}")
                            await reserve_btn.click()
                            found = True
                            break

                if found:
                    # 맥북 시스템 사운드 (성공 알림)
                    os.system('say "Reservation successful"')
                    print("✅ 예약 버튼을 눌렀습니다. 결제를 진행하세요!")
                    break

                # 6. 랜덤 대기 후 재조회 (봇 탐지 방지를 위해 1.5~2.5초 사이)
                wait_time = random.uniform(1.5, 2.5)
                await asyncio.sleep(wait_time)
                count += 1

        except Exception as e:
            print(f"❌ 에러 발생: {e}")
            await page.screenshot(path="error_screen.png")
            print("error_screen.png 파일을 확인해 보세요.")

        # 성공 후 브라우저 유지를 위해 대기
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(run_srt_automation())