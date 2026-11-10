# data/

이 폴더 안의 파일은 main 브랜치에 올리지 않습니다 (`.gitignore`).

| 경로 | 내용 | 만드는 방법 |
|---|---|---|
| `collected/raw/YYYY-MM-DD.csv` | 10분마다 쌓이는 주차장별 현재 주차 대수 | `bash scripts/sync_data.sh` |
| `collected/static/YYYY-MM-DD.csv` | 하루 한 번 저장하는 주차장 정보 전체 (주소, 요금, 운영 시간 등) | 위와 같음 |
| `processed/` | 전처리·특성 결과 (parquet 권장) | 각자 노트북·스크립트로 생성 |

`collected/`는 원격 `data` 브랜치를 가리키는 git worktree입니다. 이 안에서 직접 커밋하지 마세요. GitHub Actions만 이 브랜치에 씁니다.

## raw 열 설명

| 열 | 뜻 |
|---|---|
| `collected_at` | 수집 시각 (KST, ISO 8601) |
| `PKLT_CD` | 주차장 코드 |
| `TPKCT` | 총 주차면 |
| `NOW_PRK_VHCL_CNT` | 현재 주차 대수 |
| `NOW_PRK_VHCL_UPDT_TM` | 현재 주차 대수 갱신 시각 (KST). 오래 멈춰 있으면 연계가 끊긴 것 |
| `PRK_STTS_YN` | `1`이면 20분 이내 연계 데이터 있음 |
