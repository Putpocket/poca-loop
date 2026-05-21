# poca-loop

K-POP 팬덤용 포토카드 교환 매칭 백엔드 MVP입니다. 사용자는 보유 카드와 원하는 카드를 텍스트 메타데이터로 등록하고, 1:1 또는 3자 순환 교환 후보를 조회할 수 있습니다.

저작권 있는 포토카드 원본 이미지는 저장하거나 배포하지 않습니다. 이 프로젝트는 포토카드 텍스트 메타데이터와 검증된 외부 링크 중심으로 설계합니다.

## Screenshots

![Login screen](docs/screenshots/login.png)

![Dashboard](docs/screenshots/dashboard.png)

![Mobile dashboard](docs/screenshots/mobile-dashboard.png)

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
- React, Vite, TypeScript, Tailwind CSS
- TanStack Query, React Router, React Hook Form, Zod

## 포함된 범위

- FastAPI API 서버
- PostgreSQL 연결
- SQLAlchemy 2.x 모델
- Alembic 마이그레이션
- Docker Compose 실행 환경
- 사용자 회원가입/로그인
- Argon2 기반 비밀번호 해싱
- JWT 인증
- 관리자 전용 카탈로그 CRUD
- 포토카드 상태 등급 CRUD
- 사용자 보유 카드 등록/조회
- 사용자 원하는 카드 등록/조회
- 1:1 직접 교환 매칭 조회
- 3자 순환 교환 매칭 조회
- 로그인 사용자 텍스트 기반 공유용 체크리스트 생성
- 상태 등급 안내 UI
- 매칭 결과 기반 교환 제안 텍스트 복사
- idempotent seed 스크립트
- pytest 기본 테스트

## 제외된 범위

아래 기능은 의도적으로 구현하지 않았습니다.

- 4자 이상 다자간 매칭
- Discord 봇
- 크롤링
- LLM
- 이미지 업로드 또는 파일 업로드
- 결제, 배송, 주소 관리
- 실명 인증
- 계좌 정보 저장

특히 이미지 호스팅, 크롤링, LLM, 결제/배송 처리, 주소/실명/계좌 정보 저장은 하지 않습니다.

## 교환 대화와 안전 정책

poca-loop은 내장 채팅, DM, WebSocket 대화방을 제공하지 않습니다. 실제 대화, 실물 사진 확인, 약속 조율은 사용자가 선택한 외부 채널에서 진행합니다.

poca-loop은 거래, 배송, 결제 중개 서비스가 아니라 매칭 보조 도구입니다. 서비스 안에 주소, 계좌, 실명, 전화번호를 입력하거나 저장하지 마세요.

매칭 결과 화면의 `교환 제안 복사` 버튼은 외부 채널에 붙여넣기 쉬운 텍스트만 생성합니다. 생성 텍스트에는 이메일, 내부 DB ID, 권한 필드, 개인정보를 넣지 않습니다.

상태 등급 기준:

- `S`: 미개봉 또는 하자 없는 최상급
- `A`: 눈에 띄는 하자 없음, 아주 미세한 생활 기스 가능
- `B`: 작은 스크래치/찍힘/인쇄 밀림 등 경미한 하자 있음
- `C`: 눈에 띄는 찍힘, 눌림, 모서리 손상, 표면 흠집 있음
- `D`: 접힘, 오염, 큰 찍힘, 물결, 심한 손상 있음

최종 상태 판단은 교환 당사자가 외부 채널에서 실물 사진으로 직접 확인해야 합니다.

## 카탈로그 릴리즈/출처 메타데이터

포토카드 출처는 정식 릴리즈뿐 아니라 POB, 럭드, 공방, 팝업, 팬싸, MD처럼 다양합니다. poca-loop은 `source_type`을 큰 분류로만 두고, 실제 세부 구분은 별도 출처 메타데이터 필드에 저장합니다.

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

팝업 포카 예시:

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

POB 예시:

```yaml
source_type: preorder_benefit
title: "Fe3O4: BREAK"
retailer_or_event: Apple Music
country: KR
round: 예약판매
detail: POB A ver.
```

공방 예시:

```yaml
source_type: broadcast
title: DASH 활동
retailer_or_event: MBC 쇼! 음악중심
country: KR
round: 2024-01-20
detail: 공방 참여 특전
```

기존 API의 `release_type` 필드는 호환성을 위해 유지하지만, 새 문서와 사용자 화면에서는 “릴리즈/출처”와 `source_type`을 기준으로 표현합니다.

## 임시 포카

정식 카탈로그에서 포카를 찾지 못한 사용자는 사진 없이 텍스트 기반 임시 포카를 등록할 수 있습니다. 임시 포카는 본인이 만든 항목만 조회하고 Have/Want에 사용할 수 있습니다.

임시 포카에 저장하는 정보:

- 그룹/멤버: 정식 카탈로그와 연결하거나 텍스트 이름으로 저장
- 출처 유형과 대략적인 릴리즈/출처명
- 판매처/이벤트, 장소, 회차, 상세 설명
- 카드 설명, 버전, 메모

중요 정책:

- 포토카드 사진 업로드, 이미지 저장, 이미지 공개를 하지 않습니다.
- OCR, AI 이미지 인식, 크롤링, LLM을 사용하지 않습니다.
- 임시 포카는 정식 카탈로그가 아니며 `catalog_status=pending` 상태입니다.
- 임시 포카는 현재 자동 매칭이 제한될 수 있습니다. 정식 포카 기반 매칭은 그대로 동작합니다.
- 교환 전에는 외부 채팅에서 실물 사진과 출처를 반드시 확인해야 합니다.
- 관리자 승인/병합 기능은 TODO이며, 이번 단계에서는 만들지 않았습니다.

관련 API:

```text
POST /api/v1/catalog/pending-photocards
GET  /api/v1/me/pending-photocards
```

Have/Want 등록과 수정 API는 기존 `photocard_id` 방식과 새 `pending_photocard_id` 방식을 모두 지원합니다. 단, 둘 중 하나만 보낼 수 있습니다.

## 환경변수

`.env.example`을 복사해서 `.env`를 만듭니다.

```bash
cp .env.example .env
```

주요 값:

- `SECRET_KEY`: JWT 서명용 비밀키입니다. `.env.example` 값은 예시이며 운영에서는 긴 랜덤 문자열로 바꾸세요.
- `DATABASE_URL`: SQLAlchemy PostgreSQL 연결 문자열입니다.
- `REDIS_URL`: Redis 연결 문자열입니다. 1단계에서는 구조 준비용입니다.
- `BACKEND_CORS_ORIGINS`: 허용할 CORS origin 목록입니다. Vite dev server를 쓰면 `http://localhost:5173` 또는 LAN 접속 origin을 추가합니다.
- `SEED_ADMIN_EMAIL`: seed 스크립트가 만들 관리자 이메일입니다.
- `SEED_ADMIN_USERNAME`: seed 스크립트가 만들 관리자 username입니다.
- `SEED_ADMIN_PASSWORD`: seed 스크립트가 만들 관리자 비밀번호입니다. 운영에서는 반드시 바꾸세요.

`.env`는 Git에 커밋하지 않습니다.

## Local venv development

```bash
cp .env.example .env
make install
```

로컬 venv 개발은 Docker 권한이 없어도 가능합니다. PostgreSQL/Redis는 둘 중 하나로 준비합니다.

- 호스트에 PostgreSQL/Redis를 직접 설치해서 실행
- 또는 DB/Redis만 별도로 Docker Compose 등으로 실행

`.env`에서 로컬 개발용 값을 사용합니다.

```text
DATABASE_URL=postgresql+psycopg://pocaloop:pocaloop_example_password@localhost:5432/pocaloop
REDIS_URL=redis://localhost:6379/0
```

마이그레이션과 seed를 실행합니다.

```bash
make migrate
make seed
```

개발 서버를 실행합니다.

```bash
make dev
```

API 서버:

```text
http://localhost:8000
```

헬스 체크:

```bash
curl http://localhost:8000/health
```

OpenAPI 문서:

```text
http://localhost:8000/docs
```

## Frontend development

프론트엔드는 `frontend/` 디렉터리에 분리되어 있습니다. 백엔드 API는 기본적으로 `http://localhost:8000`을 호출합니다.

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 여세요.

```text
http://localhost:5173
http://192.168.10.203:5173
```

같은 서버에서 브라우저를 열어 `http://localhost:5173`로 접속할 때는 기본 API 주소를 그대로 둘 수 있습니다.

```text
VITE_API_BASE_URL=http://localhost:8000
```

다른 기기에서 LAN 주소인 `http://192.168.10.203:5173`로 접속하면, 그 기기의 `localhost`는 서버가 아니라 접속한 기기 자신을 뜻합니다. 이 경우 `frontend/.env`에 서버 LAN IP를 API 주소로 지정합니다.

```text
VITE_API_BASE_URL=http://192.168.10.203:8000
```

백엔드 `.env`의 CORS origin에도 Vite dev server 주소를 추가해야 합니다.

```text
# 로컬 브라우저 접속
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:8000

# LAN 브라우저 접속
BACKEND_CORS_ORIGINS=http://localhost:5173,http://192.168.10.203:5173
```

프로덕션 빌드:

```bash
cd frontend
npm run build
```

현재 프론트엔드는 MVP 편의를 위해 JWT access token을 `localStorage`에 저장합니다. XSS가 발생하면 토큰이 탈취될 수 있으므로, 운영 전에는 httpOnly secure cookie 기반 세션 또는 토큰 저장 방식으로 전환해야 합니다.

API 실패 시 화면에는 서버의 `detail` 메시지 또는 기본 오류 문구를 표시합니다. 로그인 토큰이 없으면 보호 페이지는 `/login`으로 이동합니다.

TODO:

- httpOnly cookie 인증으로 전환
- 관리자 카탈로그 UI는 별도 단계에서 검토

## Docker Compose deployment

Docker Compose는 개발 서버에서 DB까지 포함해 한 번에 띄우는 배포/검증 경로입니다. 구성 서비스는 다음과 같습니다.

- `frontend`: Vite 빌드 결과를 Nginx로 정적 서빙
- `api`: FastAPI, Alembic migration, seed 자동 실행
- `db`: PostgreSQL
- `redis`: Redis

OpenClaw 계정에 Docker 권한이 없는 환경에서는 이 단계는 건너뛰고 Local venv development를 사용하세요.

Docker 배포용 환경 파일은 `.env.deploy`를 권장합니다. `.env`는 로컬 venv 개발용으로 남겨둘 수 있고, `.env.deploy`는 Git에 커밋하지 않습니다.

`.env.deploy`에서 Docker용 DB/Redis URL은 `COMPOSE_DATABASE_URL`, `COMPOSE_REDIS_URL`로 분리되어 있습니다. 그래서 로컬 venv용 `DATABASE_URL`, `REDIS_URL` 값을 그대로 둬도 Compose 컨테이너는 내부 `db`, `redis` 서비스를 사용합니다.

```text
COMPOSE_DATABASE_URL=postgresql+psycopg://pocaloop:pocaloop_example_password@db:5432/pocaloop
COMPOSE_REDIS_URL=redis://redis:6379/0
FRONTEND_API_BASE_URL=
FRONTEND_PORT=8080
```

Compose 설정 검증:

```bash
cp .env.example .env.deploy
# SECRET_KEY, SEED_ADMIN_PASSWORD는 반드시 바꾸세요.
docker compose --env-file .env.deploy config
```

실행:

```bash
docker compose --env-file .env.deploy up --build -d
```

컨테이너 시작 시 `alembic upgrade head`와 `python -m app.db.seed`가 자동 실행됩니다.

접속:

```text
Frontend: http://localhost:8080
LAN Frontend: http://192.168.10.203:8080
API health: http://localhost:8000/health
```

Compose 프론트엔드는 같은 origin에서 API를 호출합니다. Nginx가 `/api`, `/matches`, `/templates`, `/health` 요청을 FastAPI 컨테이너로 프록시하므로 브라우저에서 별도 `VITE_API_BASE_URL`을 지정하지 않아도 됩니다.

로그 확인과 종료:

```bash
docker compose logs -f api frontend
docker compose --env-file .env.deploy down
```

## Troubleshooting

- `npm run dev`는 Vite 개발 서버를 계속 실행하는 장시간 명령입니다. 터미널이나 자동화 환경에서는 명령이 끝나지 않아 실패처럼 보일 수 있지만, `Local: http://localhost:5173/`가 보이면 정상입니다.
- LAN에서 프론트 화면은 열리지만 API가 실패하면 `VITE_API_BASE_URL`이 `localhost`로 남아 있거나, 백엔드 `BACKEND_CORS_ORIGINS`에 `http://192.168.10.203:5173`이 빠졌을 가능성이 큽니다.
- 백엔드가 실행 중인지 `curl http://localhost:8000/health` 또는 LAN에서는 `curl http://192.168.10.203:8000/health`로 확인합니다.

## 실행 검증 명령어

자주 쓰는 개발/검증 명령입니다.

```bash
make install
make migrate
make seed
make test
make dev
```

## Development deployment workflow

기능 추가나 수정 후에는 다음 순서로 검증하고 개발 서버에 재배포합니다.

```bash
make test
cd frontend && npm run build && cd ..
make deploy-dev
curl http://localhost:8080/health
```

테스트용 배포를 내릴 때는 컨테이너와 네트워크만 제거합니다. PostgreSQL 데이터 볼륨은 보존됩니다.

```bash
make compose-down
```

데이터까지 완전히 지워야 할 때만 별도로 `docker compose --env-file .env.deploy down -v`를 사용합니다.

Docker 임시 리소스 정리는 기본적으로 볼륨 보존형 명령을 사용합니다.

```bash
make docker-prune
```

`make docker-prune`은 `docker system prune -f`만 실행하므로 사용하지 않는 컨테이너, 네트워크, dangling 이미지, 빌드 캐시를 정리하되 PostgreSQL 볼륨은 지우지 않습니다. 이미지 전체 삭제가 필요할 때만 `make docker-prune-all`을 수동으로 사용합니다.

데모 시나리오는 [docs/demo-scenario.md](docs/demo-scenario.md)를 참고하세요.

Docker Compose 배포/검증 경로를 사용할 때는 다음 명령을 사용합니다.

```bash
docker compose --env-file .env.deploy config
docker compose --env-file .env.deploy up --build -d
```

Makefile 별칭도 제공합니다.

```bash
make compose-config
make deploy-dev
make compose-down
make docker-prune
```

`make compose-config`와 `make deploy-dev`는 `.env.deploy`가 없으면 `.env.example`에서 복사한 뒤 개발용 랜덤 `SECRET_KEY`, `SEED_ADMIN_PASSWORD`를 자동 생성합니다. 외부 공개 전에는 값을 직접 검토하세요.

## 마이그레이션과 Seed

Docker Compose로 실행하면 컨테이너 시작 시 자동으로 아래 순서가 실행됩니다.

```bash
alembic upgrade head
python -m app.db.seed
```

수동으로 실행하려면 `.env`를 설정한 뒤 다음 명령을 사용합니다.

```bash
make migrate
make seed
```

Seed는 여러 번 실행해도 중복 생성되지 않습니다. 생성되는 기본 데이터:

- 관리자 계정 1개
- 상태 등급 `S`, `A`, `B`, `C`, `D`
- 샘플 그룹/멤버/릴리즈/포토카드 메타데이터

## 테스트

테스트는 SQLite in-memory DB를 사용해서 빠르게 실행됩니다.

```bash
make test
```

프론트엔드 검증:

```bash
cd frontend
npm install
npm run build
```

## 주요 API

버전 prefix가 있는 API는 `/api/v1` 아래에도 제공됩니다. 예를 들어 `/api/v1/auth/signup`, `/api/v1/matches/direct`를 사용할 수 있습니다.

```text
GET  /health
POST /api/v1/auth/signup      # register
POST /api/v1/auth/login
GET  /api/v1/auth/me
GET  /matches/direct
GET  /matches/three-way
GET  /templates/me.svg
```

요구사항에서 `/auth/register`로 부르던 회원가입 동작은 현재 구현 경로 기준으로 `POST /api/v1/auth/signup`입니다.

`/matches/direct`, `/matches/three-way`, `/templates/me.svg`는 로그인한 사용자 본인의 데이터 기준으로만 응답합니다.

## 관리자 계정

카탈로그 쓰기 API는 `role=admin` 사용자만 접근할 수 있습니다. 공개 관리자 생성 API는 두지 않았고, 관리자 계정은 seed 스크립트로 생성합니다.

일반 사용자는 다음 API로 가입/로그인합니다.

```text
POST /api/v1/auth/signup
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

카탈로그 조회는 공개이고, 생성/수정/삭제는 관리자 JWT가 필요합니다.

## 보안 주의사항

- `.env`는 Git에 커밋하지 않습니다. `.env.example`만 공개합니다.
- `SECRET_KEY`, DB 비밀번호, seed 관리자 비밀번호는 운영에서 반드시 교체합니다.
- 비밀번호는 Argon2 기반 해시로 저장하며 평문 저장하지 않습니다.
- CORS 기본값은 localhost만 허용합니다. 운영 도메인은 명시적으로 추가하세요.
- 일반 응답에는 `hashed_password`, 내부 권한 필드, 토큰 서명키, 환경변수 값을 포함하지 않습니다.
- 매칭 및 체크리스트 API는 로그인한 사용자 본인의 데이터만 반환합니다.

## GitHub 업로드 전 점검

업로드 전 아래 명령으로 추적 상태, 무시 파일, 민감 문자열을 점검합니다.

```bash
git status --ignored
find . -name ".env" -o -name "*.db" -o -name "*.sqlite" -o -name "__pycache__" -o -name ".venv"
grep -R "SECRET_KEY\\|password\\|token\\|api_key" -n . --exclude-dir=.git --exclude-dir=.venv
make test
```

`.env`, 로컬 DB 파일, 캐시 디렉터리, 가상환경은 커밋하지 않습니다.

## License

License: TBD

MIT License를 사용할지 결정한 뒤 `LICENSE` 파일을 추가하세요.

## 1:1 직접 매칭

로그인한 사용자는 자신의 보유/원함 목록 기준으로 가능한 1:1 교환 후보만 조회할 수 있습니다. 다른 사용자들끼리의 매칭이나 전체 매칭 목록은 반환하지 않습니다.

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  http://localhost:8000/matches/direct
```

기본 `limit`은 50이고 최대값은 100입니다. 데이터가 많을수록 `limit`을 명시하는 것을 권장합니다.

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  "http://localhost:8000/matches/direct?limit=25"
```

응답 예시:

```json
[
  {
    "match_type": "direct",
    "user_a": {"id": 1, "username": "collector_a"},
    "user_b": {"id": 2, "username": "collector_b"},
    "user_a_gives": {"photocard": {"id": 1, "group_id": 1, "member_id": 1, "release_id": 1, "name": "Card X", "version": "A", "external_url": null, "notes": null}, "condition_grade": {"id": 2, "code": "A", "label": "A", "description": null, "sort_order": 20}},
    "user_a_receives": {"photocard": {"id": 2, "group_id": 1, "member_id": 1, "release_id": 1, "name": "Card Y", "version": "B", "external_url": null, "notes": null}, "condition_grade": {"id": 2, "code": "A", "label": "A", "description": null, "sort_order": 20}},
    "user_b_gives": {"photocard": {"id": 2, "group_id": 1, "member_id": 1, "release_id": 1, "name": "Card Y", "version": "B", "external_url": null, "notes": null}, "condition_grade": {"id": 2, "code": "A", "label": "A", "description": null, "sort_order": 20}},
    "user_b_receives": {"photocard": {"id": 1, "group_id": 1, "member_id": 1, "release_id": 1, "name": "Card X", "version": "A", "external_url": null, "notes": null}, "condition_grade": {"id": 2, "code": "A", "label": "A", "description": null, "sort_order": 20}},
    "condition_check": {
      "user_a_give_meets_user_b_minimum": true,
      "user_b_give_meets_user_a_minimum": true,
      "user_a_give_grade": "A",
      "user_b_minimum_grade": "B",
      "user_b_give_grade": "A",
      "user_a_minimum_grade": "B"
    },
    "generated_at": "2026-05-21T01:17:00Z"
  }
]
```

상태 등급 우선순위는 `S > A > B > C > D`입니다. `D` 등급은 상대가 명시적으로 `D` 이상을 허용한 경우에만 매칭됩니다.

## 3자 순환 매칭

로그인한 사용자는 자신이 참여한 `A -> B -> C -> A` 형태의 3자 교환 후보만 조회할 수 있습니다. 4자 이상 다자간 매칭이나 전체 매칭 조회 API는 아직 없습니다.

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  http://localhost:8000/matches/three-way
```

기본 `limit`은 50이고 최대값은 100입니다. 데이터가 많을수록 `limit`을 명시하는 것을 권장합니다.

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  "http://localhost:8000/matches/three-way?limit=25"
```

응답 예시:

```json
[
  {
    "match_type": "three_way",
    "participants": [
      {"id": 1, "username": "collector_a"},
      {"id": 2, "username": "collector_b"},
      {"id": 3, "username": "collector_c"}
    ],
    "trade_edges": [
      {
        "giver": {"id": 2, "username": "collector_b"},
        "receiver": {"id": 1, "username": "collector_a"},
        "card": {"id": 2, "group_id": 1, "member_id": 1, "release_id": 1, "name": "B Card", "version": null, "external_url": null, "notes": null},
        "condition_grade": {"id": 2, "code": "A", "label": "A", "description": null, "sort_order": 20},
        "receiver_min_condition_grade": {"id": 3, "code": "B", "label": "B", "description": null, "sort_order": 30},
        "condition_passed": true
      }
    ],
    "generated_at": "2026-05-21T01:24:00Z"
  }
]
```

`trade_edges`는 실제 카드 이동 방향입니다. 예시는 한 edge만 줄였지만 실제 응답은 3개 edge를 포함합니다. 같은 순환은 `A-B-C`, `B-C-A`, `C-A-B` 형태로 중복 반환되지 않습니다.

## 공유용 체크리스트

로그인한 사용자는 자신의 보유 카드와 원하는 카드 목록을 텍스트 기반 공유용 체크리스트로 받을 수 있습니다. 체크리스트는 로그인한 사용자 본인 데이터만 렌더링하며, 저작권 있는 포토카드 이미지, 외부 이미지, 외부 CSS, 외부 폰트를 사용하지 않습니다.

사용자 화면에서는 이 기능을 `공유용 체크리스트` 또는 `체크리스트 이미지`로 표현합니다.

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  http://localhost:8000/templates/me.svg \
  -o checklist.svg
```

기존 prefix 경로도 사용할 수 있습니다.

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  http://localhost:8000/api/v1/templates/me.svg \
  -o checklist.svg
```

기술적으로 이 체크리스트는 `/templates/me.svg`에서 생성되는 SVG 응답입니다. 응답은 `image/svg+xml` 계열 Content-Type과 `Cache-Control: private, no-store` 헤더를 사용합니다. 내용에는 `username`, HAVE/WANT 카드 메타데이터, 상태 등급만 들어가며 이메일이나 권한 필드는 포함하지 않습니다.
