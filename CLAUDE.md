# SVM_Project

서울시 시영주차장 실시간 주차대수(OA-21709)로 30분 뒤 혼잡도(여유·보통·혼잡)를 예측하는 SVM 팀 프로젝트. 개요와 설정 방법은 README.md 참고.

## 규칙

- 커밋과 PR에 Claude 관련 표시를 넣지 않는다 (`Co-Authored-By: Claude`, "Generated with Claude Code" 모두 금지).
- 팀 저장소(haksik-yummy/SVM_Project)이므로 push 전에 사용자에게 확인한다.
- `data/collected/`는 `data` 브랜치의 worktree다. 여기에 직접 커밋하지 않는다. GitHub Actions만 쓴다.
- `src/collect.py`는 표준 라이브러리만 쓴다 (Actions에서 설치 없이 실행).
- 인증키는 `.env` 또는 Actions secret `SEOUL_API_KEY`. 코드와 커밋에 넣지 않는다.

## 환경

- conda 환경 `svm-parking` (Python 3.12): `conda run -n svm-parking python ...`
- 수집기 점검: `python src/collect.py --sample --dry-run`

## 모델링 원칙

- 학습·테스트는 시간 순서로 나눈다. 무작위 분할 금지 (`TimeSeriesSplit`).
- 기준선("지금 혼잡도 그대로")을 항상 함께 보고한다.
- SVC는 수만 건을 넘기면 느리다. 30분 단위로 줄이고 표본으로 튜닝하거나 Nystroem + LinearSVC를 쓴다.
