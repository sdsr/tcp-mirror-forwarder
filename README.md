# EDMS TCP Forwarder (Mirror)

ED 장비가 전송하는 TCP 데이터를 **동시에 두 곳으로 미러링(복제)** 하는 포워더입니다.

기본 구조는 다음과 같습니다:

ED ──▶ Forwarder (192.168.10.23:8501)
├─▶ EDMS Server (192.168.10.23:8500)
└─▶ Developer PC (192.168.10.6:8500)


ED는 단일 목적지(IP:PORT)만 설정할 수 있기 때문에,  
중간에 **Forwarder**를 두고 데이터를 다중 목적지로 복제 전송하는 구조입니다.

이 프로젝트의 목표는:

- EDMS의 기본 포트(8500)를 유지하면서  
- 내 PC에서도 동일한 데이터를 **실시간으로 동시에 수신**할 수 있게 하고  
- 네트워크/코드 변경 없이 안전하게 테스트 환경을 구성하는 것입니다.

---

## ✨ Features

- TCP 스트림 실시간 미러링
- 무제한 목적지 복사 가능 (현재 2곳)
- 목적지 소켓 연결 실패 자동 무시
- CLI 인자로 동적 포트 지정 가능
- 시스템 변경 최소화 (EDMS는 포트만 유지)
- 간단한 Python 소켓 기반 (추가 모듈 없음)

---

## 📦 Requirements

- Python 3.7+
- 추가 패키지 없음 (순수 표준 라이브러리 사용)

---

## 🚀 Installation

```bash
git clone https://github.com/YOUR_ID/edms-forwarder.git
cd edms-forwarder

▶️ Usage
기본 실행 (기본값 그대로)
python forwarder.py


기본 동작:

Forwarder 리슨: 0.0.0.0:8501

EDMS 전송: 192.168.10.23:8500

내 PC 전송: 192.168.10.6:8500

ED 장비는 아래로 전송해야 합니다:

192.168.10.23:8501

모든 설정을 직접 지정하고 싶다면
python forwarder.py \
  --listen-ip 0.0.0.0 \
  --listen-port 9000 \
  --edms-ip 192.168.10.23 \
  --edms-port 8500 \
  --mypc-ip 192.168.10.6 \
  --mypc-port 8500


모든 인자 설명:

인자	기본값	설명
--listen-ip	0.0.0.0	포워더가 ED 데이터를 받을 IP
--listen-port	8501	포워더가 리슨할 포트
--edms-ip	192.168.10.23	EDMS 서버 IP
--edms-port	8500	EDMS 서버 포트
--mypc-ip	192.168.10.6	개발자 PC IP
--mypc-port	8500	개발자 PC 포트
🧩 Architecture
┌─────────────┐     8501      ┌──────────────┐
│     ED      │ ─────────────▶│   Forwarder   │
└─────────────┘               └──────┬───────┘
                                     │
                                     │
                       8500          │          8500
                     ┌───────────────┴──────────────┐
                     │                              │
           ┌──────────────┐               ┌────────────────┐
           │   EDMS        │               │  Developer PC  │
           └──────────────┘               └────────────────┘

📄 Code Overview

핵심 파일:

forwarder.py → TCP 패킷을 받아 여러 목적지로 복제 전송하는 메인 포워더

코드 구조:

서버 소켓(리슨)

클라이언트와 연결 발생 시 스레드 생성

목적지 소켓 연결

데이터 수신 → 목적지 모두에게 send

목적지 소켓 오류 시 자동 제거

🛠 Planned Features (Optional)

로그 파일 저장 기능

재전송 실패 시 자동 reconnect

multi-target.json 기반 동적 목적지 관리

Windows Service / systemd 자동 실행 지원

GUI 모니터링 툴(PyQt5)