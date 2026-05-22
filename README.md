# poca-loop

poca-loop은 K-POP 포토카드 교환을 위한 텍스트 기반 매칭 MVP입니다. 사용자는 보유한 포카와 원하는 포카를 등록하고, 1:1 또는 3자 순환 교환 후보를 확인할 수 있습니다.

프로젝트의 핵심 방향은 명확합니다.

- 저작권 있는 포토카드 원본 이미지를 저장하거나 배포하지 않습니다.
- 크롤링, OCR, AI/LLM 인식 없이 사용자가 입력한 텍스트 메타데이터를 사용합니다.
- 거래, 배송, 결제, 주소, 실명, 계좌 정보를 다루지 않습니다.
- poca-loop은 거래 중개 서비스가 아니라 매칭과 체크리스트를 돕는 도구입니다.

## Screenshots

아래 이미지는 GitHub 공개용 시연 이미지를 넣을 자리입니다. 현재 저장소에는 샘플 스크린샷 파일 경로만 준비되어 있습니다.

![Login screen placeholder](docs/screenshots/login.png)

![Dashboard placeholder](docs/screenshots/dashboard.png)

![Mobile dashboard placeholder](docs/screenshots/mobile-dashboard.png)

추가로 넣기 좋은 시연 이미지:

- Have/Want 등록 화면
- 1:1 매칭 화면
- 3자 매칭 화면
- 관리자 임시 포카 검토 화면
- 공유용 체크리스트 SVG 예시

## 주요 기능

사용자 기능:

- 회원가입, 로그인, JWT 인증
- 정식 카탈로그 포카 기반 Have/Want 등록, 수정, 삭제
- 카탈로그에 없는 포카의 텍스트 기반 임시 등록
- 1:1 직접 교환 후보 조회
- 3자 순환 교환 후보 조회
- 로그인 사용자 본인 데이터만 담은 공유용 체크리스트 미리보기와 SVG/PNG 다운로드
- 매칭 결과를 외부 채팅에 붙여넣기 쉬운 교환 제안 문구로 복사

관리자 기능:

- 그룹, 멤버, 릴리즈/출처, 포토카드, 상태 등급 CRUD
- 임시 포카 목록 검토
- 임시 포카 거절
- 임시 포카를 새 정식 Photocard로 승인
- 임시 포카를 기존 정식 Photocard에 병합
- 승인/병합 시 기존 UserHave/UserWant를 정식 photocard_id로 이전

매칭과 데이터 정책:

- 1:1 매칭은 로그인한 사용자가 직접 참여한 후보만 반환합니다.
- 3자 매칭은 로그인한 사용자가 포함된 순환 후보만 반환합니다.
- 임시 포카는 정식 카탈로그가 아니므로 자동 매칭에서 제외됩니다.
- 승인 또는 병합된 임시 포카는 정식 photocard_id로 이전되어 정식 포카 기반 매칭에 참여합니다.
- 상태 등급 우선순위는 `S > A > B > C > D`입니다. `D` 등급은 상대가 명시적으로 `D` 이상을 허용한 경우에만 매칭됩니다.

## 사용자 시연 흐름

1. 사용자가 회원가입하고 로그인합니다.
2. 카탈로그에서 포카를 선택해 Have를 등록합니다.
3. 원하는 포카를 Want로 등록합니다.
4. 다른 사용자의 Have/Want와 조건이 맞으면 1:1 매칭이 표시됩니다.
5. 세 명의 사용자가 순환 구조를 만들면 3자 매칭이 표시됩니다.
6. 사용자는 매칭 화면에서 교환 제안 문구를 복사해 외부 채팅에 붙여넣습니다.
7. 사용자는 본인 Have/Want 목록을 공유용 체크리스트로 미리보고 SVG 또는 PNG 파일로 다운로드합니다.
8. 다운로드한 이미지를 사용자가 선택한 SNS나 외부 채팅에 직접 올립니다.

카탈로그에 없는 포카 흐름:

1. 사용자가 사진 없이 텍스트 메타데이터로 임시 포카를 등록합니다.
2. 임시 포카를 Have 또는 Want에 연결합니다.
3. 사용자 목록에는 임시 등록/자동 매칭 제한 상태가 표시됩니다.
4. 관리자가 승인 또는 병합하면 Have/Want가 정식 photocard_id로 이전됩니다.
5. 이전 후 사용자 목록과 공유용 체크리스트에서는 정식 포카 정보가 표시됩니다.

## 관리자 시연 흐름

1. seed 관리자 계정으로 로그인합니다.
2. 그룹, 멤버, 릴리즈/출처, 포토카드, 상태 등급을 생성합니다.
3. `/admin/pending-photocards`에서 사용자가 등록한 임시 포카를 확인합니다.
4. 정식 카탈로그에 넣지 않을 항목은 거절합니다.
5. 새 정식 포카로 만들 항목은 승인합니다.
6. 이미 존재하는 정식 포카와 같은 항목은 기존 포카에 병합합니다.
7. 승인/병합 후 해당 임시 포카를 참조하던 Have/Want는 정식 photocard_id로 이전됩니다.

상태 전이:

- `pending`: 사용자가 사진 없이 텍스트로 등록한 초기 상태
- `rejected`: 관리자가 정식 카탈로그로 반영하지 않기로 한 상태
- `approved`: 관리자가 새 정식 Photocard로 승인한 상태
- `merged`: 관리자가 기존 정식 Photocard에 병합한 상태

승인/병합 중복 정리 정책:

- `UserWant`: 같은 사용자가 이미 같은 정식 `photocard_id`를 Want로 갖고 있으면 pending 기반 Want는 삭제합니다.
- `UserHave`: 같은 사용자가 이미 같은 정식 `photocard_id + condition_grade_id`를 Have로 갖고 있으면 pending 기반 Have는 삭제합니다.
- `UserHave`: 같은 정식 `photocard_id`라도 상태 등급이 다르면 둘 다 유지합니다.
- 승인/병합은 하나의 DB 트랜잭션으로 처리되어야 하며, 중간 실패 시 반쯤 이전된 상태를 남기지 않습니다.

Idempotent 정책:

- 이미 승인된 항목에 다시 요청하면 기존 승인 결과를 200으로 반환합니다.
- 이미 병합된 항목에 다시 요청하면 기존 병합 결과를 200으로 반환합니다.
- 이미 거절된 항목에 다시 거절 요청을 보내면 200으로 rejected 상태를 반환하며 새 사유가 있으면 갱신합니다.

## 하지 않는 것

아래 기능은 의도적으로 구현하지 않았습니다.

- 포토카드 이미지 업로드, 이미지 저장, 이미지 공개
- OCR, AI 이미지 인식, 크롤링, LLM
- Discord 봇
- 내장 채팅, DM, WebSocket 대화방
- 오픈채팅 링크 저장
- 공개 탐색 목록
- 교환 제안함
- 결제, 배송, 주소, 실명, 계좌 정보 저장
- 실명 인증
- 4자 이상 다자간 매칭
- 임시 포카 텍스트 자동 매칭

## 보안/저작권 정책

- `.env`, `.env.deploy`, 로컬 DB 파일, 캐시, 가상환경은 커밋하지 않습니다.
- `SECRET_KEY`, DB 비밀번호, seed 관리자 비밀번호는 운영에서 반드시 교체해야 합니다.
- 비밀번호는 Argon2 기반 해시로 저장하며 평문 저장하지 않습니다.
- JWT access token은 현재 MVP 프론트엔드에서 `localStorage`에 저장합니다. 운영 전에는 httpOnly secure cookie 기반 세션 또는 더 안전한 토큰 저장 방식으로 전환해야 합니다.
- 일반 응답에는 `hashed_password`, 내부 권한 필드, 토큰 서명키, 환경변수 값을 포함하지 않습니다.
- 매칭 및 체크리스트 API는 로그인한 사용자 본인의 데이터만 반환합니다.
- 공유용 체크리스트는 공개 링크를 만들지 않고, 로그인한 사용자가 본인 목록을 SVG/PNG 파일로 직접 다운로드하는 방식입니다.
- 체크리스트 SVG는 텍스트 렌더링이며 포토카드 이미지, 외부 이미지, 외부 CSS, 외부 폰트를 포함하지 않습니다.
- 교환 전 실물 사진, 상태, 출처 확인은 사용자가 선택한 외부 채팅에서 직접 해야 합니다.

## 기술 스택

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- Redis
- pytest
- Docker Compose
- React
- Vite
- TypeScript
- Tailwind CSS
- TanStack Query
- React Router
- React Hook Form
- Zod

## 빠른 시작

Docker Compose 개발 배포:

```bash
cp .env.example .env.deploy
# SECRET_KEY, SEED_ADMIN_PASSWORD는 반드시 바꾸세요.
docker compose --env-file .env.deploy up --build -d
```

접속:

```text
Frontend: http://localhost:8080
API health: http://localhost:8000/health
OpenAPI: http://localhost:8000/docs
```

컨테이너 시작 시 API 컨테이너가 자동으로 실행합니다.

```bash
alembic upgrade head
python -m app.db.seed
```

개발 서버를 내릴 때:

```bash
docker compose --env-file .env.deploy down
```

PostgreSQL 데이터 볼륨까지 지울 때만 수동으로 `down -v`를 사용하세요.

## 로컬 venv 개발

```bash
cp .env.example .env
make install
make migrate
make seed
make dev
```

로컬 venv 개발용 `.env` 예시:

```text
DATABASE_URL=postgresql+psycopg://pocaloop:pocaloop_example_password@localhost:5432/pocaloop
REDIS_URL=redis://localhost:6379/0
```

프론트엔드 개발:

```bash
cd frontend
npm install
npm run dev
```

기본 프론트엔드 개발 주소:

```text
http://localhost:5173
```

LAN 기기에서 접속할 때는 `frontend/.env`에 서버 주소를 지정합니다.

```text
VITE_API_BASE_URL=http://<server-lan-ip>:8000
```

백엔드 `.env`의 `BACKEND_CORS_ORIGINS`에도 해당 Vite origin을 추가해야 합니다.

## 주요 API

인증:

```text
POST /api/v1/auth/signup
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

카탈로그:

```text
GET  /api/v1/catalog/groups
GET  /api/v1/catalog/members
GET  /api/v1/catalog/releases
GET  /api/v1/catalog/photocards
POST /api/v1/catalog/groups              # admin
POST /api/v1/catalog/members             # admin
POST /api/v1/catalog/releases            # admin
POST /api/v1/catalog/photocards          # admin
```

사용자 카드:

```text
GET    /api/v1/me/cards/haves
POST   /api/v1/me/cards/haves
PATCH  /api/v1/me/cards/haves/{id}
DELETE /api/v1/me/cards/haves/{id}
GET    /api/v1/me/cards/wants
POST   /api/v1/me/cards/wants
PATCH  /api/v1/me/cards/wants/{id}
DELETE /api/v1/me/cards/wants/{id}
```

매칭과 체크리스트:

```text
GET /matches/direct
GET /matches/three-way
GET /templates/me.svg
GET /api/v1/templates/me.svg
```

임시 포카:

```text
POST /api/v1/catalog/pending-photocards
GET  /api/v1/me/pending-photocards
GET  /api/v1/admin/pending-photocards?limit=50
POST /api/v1/admin/pending-photocards/{id}/approve
POST /api/v1/admin/pending-photocards/{id}/merge
POST /api/v1/admin/pending-photocards/{id}/reject
```

## 릴리즈/출처 메타데이터

포토카드 출처는 정식 릴리즈뿐 아니라 POB, 럭드, 공방, 팝업, 팬싸, MD처럼 다양합니다. poca-loop은 `source_type`을 큰 분류로 두고, 실제 세부 구분은 별도 출처 메타데이터 필드에 저장합니다.

지원하는 `source_type`:

```text
album
preorder_benefit
store_benefit
lucky_draw
fansign
broadcast
popup
concert
fanmeeting
merch
season_greeting
fanclub
collab
magazine
event
other
```

세부 필드:

- `retailer_or_event`: 판매처, 이벤트명, 방송명 등
- `venue`: 장소
- `country`: 국가 또는 지역 코드
- `round`: 회차, 예약판매, 날짜 등
- `detail`: 구매 조건, 버전, 특전 조건 등
- `start_date`, `end_date`: 기간
- `notes`: 운영 메모

예시:

```yaml
source_type: popup
title: "Fe3O4: BREAK POP-UP STORE"
retailer_or_event: JYP SHOP
venue: The Hyundai Seoul
country: KR
round: 1차
detail: 5만원 이상 구매 특전
notes: 랜덤 포토카드 세트
```

기존 API의 `release_type` 필드는 호환성을 위해 유지하지만, 새 문서와 사용자 화면에서는 “릴리즈/출처”와 `source_type`을 기준으로 표현합니다.

## 교환 안전 안내

poca-loop은 내장 채팅을 제공하지 않습니다. 실제 대화, 실물 사진 확인, 약속 조율은 사용자가 선택한 외부 채널에서 진행합니다.

매칭 결과 화면의 `교환 제안 복사` 버튼은 외부 채널에 붙여넣기 쉬운 텍스트만 생성합니다. 생성 텍스트에는 이메일, 내부 DB ID, 권한 필드, 개인정보를 넣지 않습니다.

상태 등급 기준:

- `S`: 미개봉 또는 하자 없는 최상급
- `A`: 눈에 띄는 하자 없음, 아주 미세한 생활 기스 가능
- `B`: 작은 스크래치/찍힘/인쇄 밀림 등 경미한 하자 있음
- `C`: 눈에 띄는 찍힘, 눌림, 모서리 손상, 표면 흠집 있음
- `D`: 접힘, 오염, 큰 찍힘, 물결, 심한 손상 있음

최종 상태 판단은 교환 당사자가 외부 채널에서 실물 사진으로 직접 확인해야 합니다.

## 테스트/검증

백엔드 테스트:

```bash
make test
```

프론트엔드 빌드:

```bash
cd frontend
npm run build
```

Docker 배포 검증:

```bash
docker compose --env-file .env.deploy ps
docker compose --env-file .env.deploy exec api alembic current
curl http://localhost:8000/health
```

최근 검증 상태:

- `make test`: 95 passed
- `npm run build`: 통과
- Docker Compose: api/db/redis/frontend Up
- DB healthcheck: healthy
- Alembic: `202605220001 (head)`
- `/health`: `{"status":"ok","database":"ok"}`
- 실제 API 스모크: 회원가입/로그인, Have/Want CRUD, 1:1 매칭, 3자 매칭, SVG 체크리스트, 임시 포카 reject/approve/merge, 오류 정책 확인

## 데모 시나리오

자세한 시연 순서는 [docs/demo-scenario.md](docs/demo-scenario.md)를 참고하세요.

추천 GitHub 데모 흐름:

1. 로그인 화면에서 일반 사용자로 로그인합니다.
2. Have/Want를 등록합니다.
3. 1:1 매칭과 3자 매칭을 확인합니다.
4. 교환 제안 문구를 복사합니다.
5. 공유용 체크리스트를 미리보고 SVG 또는 PNG 파일로 다운로드합니다.
6. 임시 포카를 등록합니다.
7. 관리자 화면에서 임시 포카를 승인 또는 병합합니다.
8. 사용자 목록에서 임시 배지가 사라지고 정식 포카로 표시되는지 확인합니다.

## GitHub 공개 전 점검

```bash
git status --ignored
find . -name ".env" -o -name "*.db" -o -name "*.sqlite" -o -name "__pycache__" -o -name ".venv"
grep -R "SECRET_KEY\\|password\\|token\\|api_key" -n . --exclude-dir=.git --exclude-dir=.venv
make test
```

`.env`, `.env.deploy`, 로컬 DB 파일, 캐시 디렉터리, 가상환경은 커밋하지 않습니다.

## License

License: TBD

MIT License를 사용할지 결정한 뒤 `LICENSE` 파일을 추가하세요.
