# SVM_Project

서울 열린데이터 광장의 [서울시 시영주차장 실시간 주차대수 정보(OA-21709)](http://data.seoul.go.kr/dataList/OA-21709/S/1/datasetView.do)로 주차장 혼잡도 분류기를 만드는 프로젝트입니다.

## 문제 정의

- 점유율 = 현재 주차 대수 ÷ 총 주차면
- 혼잡도 3단계: 여유(50% 미만), 보통(50~85%), 혼잡(85% 이상). 기준은 데이터 분포를 보고 조정합니다.
- 예측 대상: **30분 뒤 혼잡도**. 현재 혼잡도는 나눗셈 한 번으로 나오므로 모델을 쓸 이유가 없습니다.
- 비교 모델: 기준선(최빈 클래스, "지금 그대로") → LinearSVC → RBF SVC → SVR 예측 후 구간 나누기
- 평가: 시간 순서대로 나눈 학습·테스트 세트, macro F1, 클래스별 재현율, 혼동 행렬

## 데이터 수집

이 API는 과거 데이터를 제공하지 않아서 직접 쌓아야 합니다. GitHub Actions가 10분마다 `src/collect.py`를 실행해 결과를 `data` 브랜치에 커밋합니다 ([collect.yml](.github/workflows/collect.yml)).

수집을 시작하려면 저장소 관리자가 한 번만 설정하면 됩니다.

1. [서울 열린데이터 광장](https://data.seoul.go.kr)에서 일반 인증키를 발급받습니다.
2. 저장소 Settings > Secrets and variables > Actions에 `SEOUL_API_KEY`라는 이름으로 등록합니다.
3. Actions 탭에서 `collect-parking`을 수동 실행해 성공하는지 확인합니다. "sample 키로 접속만 확인"을 켜면 인증키 없이 접속만 점검합니다.

GitHub 예약 실행은 몇 분씩 늦거나 가끔 빠질 수 있으니, 전처리에서 `collected_at` 간격을 확인하세요.

## 개발 환경

```bash
git clone https://github.com/haksik-yummy/SVM_Project.git
cd SVM_Project

conda create -n svm-parking -c conda-forge python=3.12 -y
conda activate svm-parking
pip install -r requirements.txt

bash scripts/sync_data.sh   # 수집된 데이터를 data/collected/ 로 내려받기 (다시 실행하면 최신으로 갱신)
```

수집기를 로컬에서 직접 돌려 보려면 `.env.example`을 `.env`로 복사해 인증키를 넣습니다.

```bash
python src/collect.py --sample --dry-run   # 인증키 없이 응답 확인 (5건)
python src/collect.py --dry-run            # 내 인증키로 전체 122건 확인
```

## 폴더 구조

```
.github/workflows/collect.yml   10분 주기 수집 워크플로
src/collect.py                  수집기 (표준 라이브러리만 사용)
scripts/sync_data.sh            data 브랜치를 data/collected/ 로 동기화
data/                           데이터 (git 제외, data/README.md 참고)
notebooks/                      탐색·실험 노트북
requirements.txt                분석·학습용 패키지
```

## 일정

| 시기 | 할 일 |
|---|---|
| 1주차 | 인증키 발급, 수집기 가동, 첫 며칠 분량 살펴보기 |
| 2~3주차 | 수집 계속, 전처리와 특성 코드 작성, 작은 데이터로 파이프라인 완성 |
| 4주차 | 본 학습, 튜닝, SVC와 SVR 비교 |
| 5주차 | 결과 분석, 시각화, 보고서 |
