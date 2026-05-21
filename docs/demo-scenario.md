# poca-loop demo scenario

이 문서는 홈서버 개발 배포에서 빠르게 화면과 API 흐름을 확인하기 위한 데모 절차입니다.

## 1. Deploy

```bash
make deploy-dev
curl http://localhost:8080/health
```

정상 응답:

```json
{"status":"ok","database":"ok"}
```

## 2. Open the UI

```text
http://localhost:8080
http://192.168.10.203:8080
```

LAN에서 접속할 때도 Compose 프론트엔드는 같은 origin Nginx 프록시를 사용하므로 별도 `VITE_API_BASE_URL` 설정이 필요 없습니다.

## 3. Create a demo user

UI에서 회원가입합니다.

```text
Email: demo@example.com
Username: demo_user
Password: demo-password-change-me
```

이미 같은 이메일이 있다면 다른 이메일을 사용하세요. 이 값은 데모용 예시이며 운영용 비밀번호로 쓰면 안 됩니다.

## 4. Confirm dashboard behavior

로그인 후 대시보드에서 다음을 확인합니다.

- Have, Want, 1:1 matches, 3-way matches 카운터가 표시됩니다.
- 데이터가 없으면 `0`으로 보입니다.
- `SVG 열기` 버튼이 로그인한 사용자 본인의 텍스트 기반 SVG 체크리스트를 엽니다.
- 로그아웃 후 `/dashboard`로 직접 접근하면 `/login`으로 이동합니다.

## 5. Seeded catalog reference

기본 seed는 아래 카탈로그 메타데이터를 만듭니다.

- Group: `NewJeans`
- Member: `Minji`
- Release: `Get Up`
- Photocard: `Bunny Beach`, version `Sample`
- Condition grades: `S`, `A`, `B`, `C`, `D`

관리자 카탈로그 UI는 아직 없으므로, 일반 UI의 보유/원함 등록은 기존 카탈로그 ID를 입력하는 MVP 형태입니다.

## 6. Cleanup

테스트 배포를 내립니다. DB 볼륨은 보존됩니다.

```bash
make compose-down
```

사용하지 않는 Docker 빌드 캐시와 중지된 리소스를 정리합니다. DB 볼륨은 지우지 않습니다.

```bash
make docker-prune
```

이미지까지 강하게 지울 때만 아래 명령을 수동으로 사용합니다.

```bash
make docker-prune-all
```
