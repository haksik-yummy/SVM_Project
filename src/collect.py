"""서울시 시영주차장 실시간 주차대수(GetParkingInfo, OA-21709) 수집기.

한 번 실행하면 API를 한 번 불러서 아래 두 파일에 기록한다.
  <out-dir>/raw/YYYY-MM-DD.csv     매 실행마다 주차장별 현재 주차 대수를 한 줄씩 추가
  <out-dir>/static/YYYY-MM-DD.csv  하루 한 번, 응답 전체 필드(주소, 요금, 운영 시간 등)를 저장

GitHub Actions에서 의존성 설치 없이 돌도록 표준 라이브러리만 쓴다.

사용 예:
  python src/collect.py                        # .env 또는 환경변수의 SEOUL_API_KEY 사용
  python src/collect.py --sample --dry-run     # 공개 sample 키(최대 5건)로 응답만 확인
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
BASE_URL = "http://openapi.seoul.go.kr:8088/{key}/json/GetParkingInfo/{start}/{end}/"
PAGE_SIZE = 1000  # 서울 열린데이터 광장 API의 1회 요청 최대 건수
SAMPLE_KEY = "sample"
SAMPLE_MAX_ROWS = 5  # sample 키는 5건까지만 내려준다

# 매 실행마다 기록하는 필드 (나머지는 static 스냅샷에만 저장)
DYNAMIC_FIELDS = [
    "PKLT_CD",  # 주차장 코드
    "TPKCT",  # 총 주차면
    "NOW_PRK_VHCL_CNT",  # 현재 주차 대수
    "NOW_PRK_VHCL_UPDT_TM",  # 현재 주차 대수 갱신 시각 (KST)
    "PRK_STTS_YN",  # 1이면 20분 이내 연계 데이터 있음
]
RAW_HEADER = ["collected_at", *DYNAMIC_FIELDS]

REPO_ROOT = Path(__file__).resolve().parent.parent


class ApiError(RuntimeError):
    pass


def load_api_key() -> str | None:
    """환경변수 SEOUL_API_KEY, 없으면 저장소 루트 .env 파일에서 읽는다."""
    key = os.environ.get("SEOUL_API_KEY", "").strip()
    if key:
        return key
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == "SEOUL_API_KEY":
                return value.strip().strip("'\"") or None
    return None


def parse_response(text: str) -> dict:
    """JSON 응답을 dict로 바꾼다.

    인증키 오류 등은 json을 요청해도 XML(<RESULT><CODE>..)로 오므로 같은 모양의 dict로 맞춘다.
    """
    text = text.strip()
    if text.startswith("<"):
        root = ET.fromstring(text)
        return {"RESULT": {"CODE": root.findtext("CODE", ""), "MESSAGE": root.findtext("MESSAGE", "")}}
    return json.loads(text)


def fetch_page(key: str, start: int, end: int, retries: int = 3) -> dict:
    url = BASE_URL.format(key=key, start=start, end=end)
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                return parse_response(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ET.ParseError) as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(2 * attempt)
    raise ApiError(f"API 요청 실패 ({retries}회 시도): {last_exc}")


def check_result(payload: dict) -> dict:
    """응답 코드를 확인하고 GetParkingInfo 본문을 돌려준다."""
    body = payload.get("GetParkingInfo")
    # 인증키 오류 같은 경우 RESULT가 최상위에 온다
    result = (body or payload).get("RESULT", {})
    code = result.get("CODE", "")
    if code != "INFO-000" or body is None:
        raise ApiError(f"API 오류 {code or '(코드 없음)'}: {result.get('MESSAGE', payload)}")
    return body


def fetch_all(key: str) -> list[dict]:
    if key == SAMPLE_KEY:
        return check_result(fetch_page(key, 1, SAMPLE_MAX_ROWS))["row"]

    rows: list[dict] = []
    start = 1
    while True:
        body = check_result(fetch_page(key, start, start + PAGE_SIZE - 1))
        rows.extend(body["row"])
        total = int(body["list_total_count"])
        start += PAGE_SIZE
        if start > total:
            break
    if len(rows) != total:
        raise ApiError(f"받은 행 수({len(rows)})가 list_total_count({total})와 다릅니다")
    return rows


def append_raw(path: Path, collected_at: str, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(RAW_HEADER)
        for row in rows:
            writer.writerow([collected_at, *(row.get(k, "") for k in DYNAMIC_FIELDS)])


def write_static(path: Path, collected_at: str, rows: list[dict]) -> bool:
    """오늘 스냅샷이 없을 때만 응답 전체 필드를 저장한다."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        fields.extend(k for k in row if k not in fields)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["collected_at", *fields])
        writer.writeheader()
        for row in rows:
            writer.writerow({"collected_at": collected_at, **row})
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "data" / "collected",
        help="raw/, static/ 폴더를 둘 위치 (기본: data/collected)",
    )
    parser.add_argument("--sample", action="store_true", help="공개 sample 키로 호출 (최대 5건)")
    parser.add_argument("--dry-run", action="store_true", help="파일에 쓰지 않고 요약만 출력")
    args = parser.parse_args()

    key = SAMPLE_KEY if args.sample else load_api_key()
    if not key:
        print("SEOUL_API_KEY가 없습니다. .env에 넣거나 환경변수로 지정하세요.", file=sys.stderr)
        return 2

    now = datetime.now(KST)
    collected_at = now.isoformat(timespec="seconds")
    try:
        rows = fetch_all(key)
    except ApiError as exc:
        print(f"[{collected_at}] {exc}", file=sys.stderr)
        return 1

    live = sum(1 for r in rows if str(r.get("PRK_STTS_YN")) == "1")
    updated = sorted({r.get("NOW_PRK_VHCL_UPDT_TM", "") for r in rows} - {""})
    print(
        f"[{collected_at}] {len(rows)}건 수신 (실시간 연계 {live}건, "
        f"갱신 시각 {updated[0] if updated else '-'} ~ {updated[-1] if updated else '-'})"
    )
    if args.dry_run:
        for r in rows[:5]:
            print("  ", {k: r.get(k) for k in ["PKLT_NM", *DYNAMIC_FIELDS]})
        return 0

    day = now.strftime("%Y-%m-%d")
    append_raw(args.out_dir / "raw" / f"{day}.csv", collected_at, rows)
    if write_static(args.out_dir / "static" / f"{day}.csv", collected_at, rows):
        print(f"  정적 정보 스냅샷 저장: static/{day}.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
