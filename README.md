# NaverCafeAttendanceCrawler
[네이버 카페](http://cafe.naver.com)에서 특정 기간 내 특정 회원이 접속(게시물/덧글 작성 또는 출석)한 날짜를 확인하는 크롤러입니다.

## Requirements
`selenium` 패키지가 설치되어 있어야 합니다.

## 사용 방법
[Youtube Tutorial](https://youtu.be/T4DCo15pErE)

1. input.txt에 평가 기간/평가 대상의 네이버 ID를 입력합니다.
2. 콘솔창에 `python main.py`를 쳐서 프로그램을 실행합니다.
3. 브라우저 창이 뜨면 로그인합니다.
4. 브라우저 창이 닫힐 때까지 기다립니다.
5. 프로그램이 정상적으로 종료되면 result.txt와 members/ 폴더에서 평가 결과를 확인합니다.
