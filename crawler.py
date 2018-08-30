from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import datetime as dt
import os

ARTICLE = -2  # 카페북 때문에 왼쪽 인덱스가 일정하지 않을 수 있음, get_dates()에서 쓰이는 상수
COMMENT = 3   # get_dates()에서 쓰이는 상수

CLUB_NAME = 'gameppt'
CLUB_ID = 16854404  # 네이버 카페 고유 ID


def get_web_driver():
    """네이버 로그인이 된 WebDriver 객체를 반환합니다. Blocking method."""
    wd = webdriver.Chrome('driver/chromedriver.exe')
    wd.implicitly_wait(1.5)
    wd.get('https://nid.naver.com/nidlogin.login')

    while not wd.current_url.startswith("https://www.naver.com/"):  # 로그인 할 때 까지 대기
        time.sleep(1)

    return wd


def to_date(str):
    """string to datetime.date"""
    if str[2:3] == ':':  # HH:MM
        return dt.datetime.now().date()
    elif str[4:5] == '.':
        return dt.datetime.strptime(str, "%Y.%m.%d.").date()
    else:
        return None


def get_dates(wd, index):
    """현재 페이지에서 작성 게시물/덧글의 작성일을 list로 구해옴"""
    try:
        return [to_date(e.find_elements_by_tag_name("td")[index].text)
                for e in wd.find_elements_by_xpath(f"//tbody/tr")]
    except IndexError:  # 작성하신 게시물이 없습니다.
        return []


def view_member_info(driver, naver_id, until=dt.date(1970, 1, 1)):
    """
    :param driver: 사용 가능한 selenium의 webdriver 객체
    :param naver_id: 조회할 멤버의 네이버 ID
    :param until: until 또는 그 이전에 작성된 게시물/덧글이 발견될 경우 탐색 종료 (~ date_from, date_start)
    :return: 해당 회원이 게시물 또는 덧글을 작성한 일자가 "yyyy.mm.dd."로 표현된 set
    """

    driver.get(f'https://cafe.naver.com/{CLUB_NAME}?' +
               f'iframe_url=/CafeMemberNetworkView.nhn%3Fm=view%26clubid={CLUB_ID}%26' +
               f'memberid={id}%26networkSearchKey=Article%26networkSearchType=7')
    driver.implicitly_wait(2)

    # 게시물 스캔
    switch_to_inner_network(driver)
    result = get_dates(driver, ARTICLE)
    while next_page(driver) and result[-1] >= until:
        result.extend(get_dates(driver, ARTICLE))
        driver.implicitly_wait(1)

    # 덧글 스캔
    switch_to_inner_network(driver)
    try:
        driver.find_element_by_xpath("(//div[@class='sort_area'])/a[3]").click()
        driver.implicitly_wait(1)

        result.extend(get_dates(driver, COMMENT))
        while next_page(driver) and result[-1] >= until:
            result.extend(get_dates(driver, COMMENT))
            driver.implicitly_wait(1)
    except NoSuchElementException:  # 탈퇴 멤버
        pass

    return set(result)


def switch_to_inner_network(driver):
    driver.switch_to.default_content()
    driver.switch_to.frame("cafe_main")
    driver.switch_to.frame("innerNetwork")


def next_page(driver, inner_network=True):
    """다음 페이지로 넘어가는 버튼을 찾고, 찾았을 경우 버튼을 누릅니다.
    다음 페이지로 넘어가는 버튼을 찾았을 경우에만 True를 반환합니다."""
    if inner_network:
        switch_to_inner_network(driver)
    button = None
    flag = False

    for elem in driver.find_elements_by_xpath("//div[@class='prev-next']/a"):
        if flag:
            button = elem
            break
        elif "on" in elem.get_attribute("class"):
            flag = True

    if button:
        driver.implicitly_wait(2)
        try:
            button.click()
        except:  # 버튼이 안 눌리면 브라우저 사각형 밖에 있다는 뜻임
            driver.switch_to_default_content()
            driver.execute_script("window.scrollBy(0, 100);")
        return True
    else:
        return False


def evaluate_member(driver, db, naver_id, date_from, date_to):
    """date_from부터 date_to까지의 활동(게시물, 덧글, 출석) 기록을 추적하여 활동량 평가를 진행합니다.
    평가 결과는 members/{naver_id}.txt에 저장됩니다.
    :return: result.txt에 저장될 한 줄 (활동률)"""
    os.makedirs("members", exist_ok=True)

    with open(f"members/{naver_id}.txt", "w", encoding="utf-8") as f:
        dates = get_dates_from_attendance_db(db, naver_id)
        dates.extend(view_member_info(driver, naver_id, until=date_from))

        result = sorted([d for d in set(dates) if date_from <= d <= date_to])
        period = (date_to - date_from).days + 1

        f.write(f"# 평가 기간: {date_from} ~ {date_to}\n")
        f.write(f"# 평가 기간 {period}일 중 {len(result)}일 출석, {len(result)/period*100:.2f}%\n\n")
        for itr in result:
            f.write(str(itr) + '\n')

    return f"{naver_id} {len(result)/period*100:.2f}%\n"


def get_attended_members(driver, d):
    """d:datetime.date 날 본 카페에 출석한 사람의 네이버 id를 읽어옵니다."""
    driver.get(f'https://cafe.naver.com/{CLUB_NAME}?' +
               f'iframe_url=/AttendanceView.nhn%3Fsearch.clubid={CLUB_ID}%26search.menuid=20%26' +
               f'search.attendyear={d.year}%26search.attendmonth={d.month}%26search.attendday={d.day}')
    driver.implicitly_wait(1)
    driver.switch_to.default_content()
    driver.switch_to.frame("cafe_main")

    def get_members():
        return [e.get_attribute('onclick').split("'")[1] for e
                in driver.find_elements_by_xpath("//td[@class='p-nick']/a")]

    result = get_members()
    while next_page(driver, inner_network=False):
        result.extend(get_members())
        driver.implicitly_wait(1)
        driver.switch_to.default_content()
        driver.switch_to.frame("cafe_main")

    return set(result)


def read_attended_members(driver, d):
    """get_attended_members()랑 같은 기능을 수행합니다.

    만약 attendance/[yyyy-mm-dd].txt 파일이 존재한다면 크롤링하는 대신 파일로부터 정보를 읽어옵니다.
    해당 파일이 존재하지 않을 경우 크롤링하고 그 결과를 파일에 새로 저장합니다. (오늘 날짜 제외)"""

    os.makedirs("attendance", exist_ok=True)
    filename = f"attendance/{d.strftime('%Y-%m-%d')}.txt"

    try:
        with open(filename, "r") as f:
            result = [line[:-1] for line in f.readlines()]
    except IOError:  # 파일이 없을 경우
        result = get_attended_members(driver, d)
        if d < dt.datetime.now().date():
            with open(filename, "w") as f:
                for itr in result:
                    f.write(itr + '\n')

    return result


def make_attendance_db(driver, date_from, date_to):
    """date_from부터 date_to까지 각각의 datetime.date에 대해 read_attended_members()를 호출합니다.
    :return: key:datetime.date, value:list(string)인 dictionary"""
    result = {}

    date_itr = date_from
    while date_itr <= date_to:
        result[date_itr] = read_attended_members(driver, date_itr)
        date_itr += dt.timedelta(days=1)

    return result


def get_dates_from_attendance_db(db, naver_id):
    """make_attendance_db()를 활용해 naver_id 계정이 출석한 날짜를 리스트로 불러옵니다."""
    return [k for k, v in db.items() if naver_id in v]
