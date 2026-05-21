# poca-loop

K-POP 팬덤용 포토카드 교환 매칭 백엔드 MVP입니다. 사용자는 보유 카드와 원하는 카드를 텍스트 메타데이터로 등록하고, 1:1 또는 3자 순환 교환 후보를 조회할 수 있습니다.

저작권 있는 포토카드 원본 이미지는 저장하거나 배포하지 않습니다. 이 프로젝트는 포토카드 텍스트 메타데이터와 검증된 외부 링크 중심으로 설계합니다.

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
- 로그인 사용자 체크리스트 SVG 생성
- idempotent seed 스크립트
- pytest 기본 테스트

## 제외된 범위

아래 기능은 의도적으로 구현하지 않았습니다.

- 4자 이상 다자간 매칭
- 프론트엔드
- Discord 봇
- 크롤링
- LLM
- 이미지 업로드 또는 파일 업로드
- 결제, 배송, 주소 관리
- 실명 인증
- 계좌 정보 저장

특히 이미지 호스팅, 크롤링, LLM, 결제/배송 처리, 주소/실명/계좌 정보 저장은 하지 않습니다.

## 환경변수

`.env.example`을 복사해서 `.env`를 만듭니다.

```bash
cp .env.example .env
```

주요 값:

- `SECRET_KEY`: JWT 서명용 비밀키입니다. `.env.example` 값은 예시이며 운영에서는 긴 랜덤 문자열로 바꾸세요.
- `DATABASE_URL`: SQLAlchemy PostgreSQL 연결 문자열입니다.
- `REDIS_URL`: Redis 연결 문자열입니다. 1단계에서는 구조 준비용입니다.
- `BACKEND_CORS_ORIGINS`: 허용할 CORS origin 목록입니다. 기본값은 localhost만 허용합니다.
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

## Docker Compose deployment

Docker Compose는 배포/검증용 경로입니다. OpenClaw 계정에 Docker 권한이 없는 환경에서는 이 단계는 건너뛰고 Local venv development를 사용하세요.

`.env`에서 Docker용 DB/Redis URL을 사용합니다.

```text
DATABASE_URL=postgresql+psycopg://pocaloop:pocaloop_example_password@db:5432/pocaloop
REDIS_URL=redis://redis:6379/0
```

Compose 설정 검증:

```bash
cp .env.example .env
docker compose config
```

실행:

```bash
docker compose up --build
```

컨테이너 시작 시 `alembic upgrade head`와 `python -m app.db.seed`가 자동 실행됩니다.

## 실행 검증 명령어

자주 쓰는 개발/검증 명령입니다.

```bash
make install
make migrate
make seed
make test
make dev
```

Docker Compose 배포/검증 경로를 사용할 때는 다음 명령을 사용합니다.

```bash
docker compose config
docker compose up --build
```

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
- 매칭 및 SVG API는 로그인한 사용자 본인의 데이터만 반환합니다.

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

## SVG 체크리스트

로그인한 사용자는 자신의 보유 카드와 원하는 카드 목록을 텍스트 기반 SVG로 받을 수 있습니다. SVG는 로그인한 사용자 본인 데이터만 렌더링하며, 저작권 있는 포토카드 이미지, 외부 이미지, 외부 CSS, 외부 폰트를 사용하지 않습니다.

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

응답은 `image/svg+xml` 계열 Content-Type과 `Cache-Control: private, no-store` 헤더를 사용합니다. SVG에는 `username`, HAVE/WANT 카드 메타데이터, 상태 등급만 들어가며 이메일이나 권한 필드는 포함하지 않습니다.
