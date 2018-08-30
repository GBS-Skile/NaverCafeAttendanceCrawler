import crawler
import datetime as dt

DATE_FORMAT = '%Y.%m.%d.\n'

with open('input.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

    date_start = dt.datetime.strptime(lines[0], DATE_FORMAT).date()
    date_end = dt.datetime.strptime(lines[1], DATE_FORMAT).date()

    if not date_start <= date_end:
        raise ValueError("date_start > date_end")

    members = []
    for line in lines[2:]:
        if line.startswith('#'):
            continue
        elif line.strip():  # remove last '\n'
            members.append(line.strip())

    # 크롤링 시작
    wd = crawler.get_web_driver()
    attend_db = crawler.make_attendance_db(wd, date_start, date_end)

    with open('result.txt', 'w', encoding='utf-8') as f:
        f.writelines(lines[:2])

        for mem in members:
            f.write(crawler.evaluate_member(wd, attend_db, mem, date_start, date_end))

    wd.close()