import socket
import threading
import argparse


def pipe(src, dst_list, direction_desc):
    """src에서 읽어서 dst_list 로 보내는 파이프"""
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break

            # 대상들로 송신
            for s in list(dst_list):
                try:
                    s.sendall(data)
                except Exception as e:
                    print(f"[WARN] Send failed ({direction_desc}) to {s}: {e}")
                    try:
                        s.close()
                    except Exception:
                        pass
                    dst_list.remove(s)

            if not dst_list:
                print(f"[WARN] No more destinations ({direction_desc}), stopping pipe.")
                break
    finally:
        try:
            src.close()
        except Exception:
            pass


def handle_client(client_sock, client_addr, edms_ip, edms_port, mirror_ip, mirror_port):
    print(f"[+] ED connected from {client_addr}")

    # 1) EDMS 에 접속 (양방향 프록시 대상)
    try:
        edms_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        edms_sock.connect((edms_ip, edms_port))
        print(f"  -> Connected to EDMS {edms_ip}:{edms_port}")
    except Exception as e:
        print(f"[ERROR] Failed to connect EDMS {edms_ip}:{edms_port} - {e}")
        client_sock.close()
        return

    # 2) 미러링용 내 PC 접속 (연결 실패해도 ED ↔ EDMS 는 그대로 진행)
    mirror_sock = None
    if mirror_ip and mirror_port:
        try:
            mirror_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mirror_sock.connect((mirror_ip, mirror_port))
            print(f"  -> Connected to Mirror {mirror_ip}:{mirror_port}")
        except Exception as e:
            print(f"[WARN] Failed to connect Mirror {mirror_ip}:{mirror_port} - {e}")
            mirror_sock = None

    # 파이프 구성
    # ED → EDMS (+ Mirror)
    dst_from_ed = [edms_sock]
    if mirror_sock:
        dst_from_ed.append(mirror_sock)

    # EDMS → ED (응답/heartbeat)
    dst_from_edms = [client_sock]

    # 스레드 2개: 양방향
    t1 = threading.Thread(
        target=pipe,
        args=(client_sock, dst_from_ed, "ED -> EDMS/Mirror"),
        daemon=True,
    )
    t2 = threading.Thread(
        target=pipe,
        args=(edms_sock, dst_from_edms, "EDMS -> ED"),
        daemon=True,
    )

    t1.start()
    t2.start()

    # 둘 다 끝날 때까지 대기
    t1.join()
    t2.join()

    print(f"[-] ED disconnected {client_addr}")

    # 정리
    for s in [edms_sock, mirror_sock]:
        if s:
            try:
                s.close()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="EDMS TCP Forwarder (bidirectional proxy + mirror)")

    parser.add_argument("--listen-ip", default="0.0.0.0")
    parser.add_argument("--listen-port", type=int, default=8501, help="포워더가 ED로부터 받는 포트")

    parser.add_argument("--edms-ip", default="192.168.10.23")
    parser.add_argument("--edms-port", type=int, default=8500)

    parser.add_argument("--mirror-ip", default="192.168.10.6")
    parser.add_argument("--mirror-port", type=int, default=8500)

    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.listen_ip, args.listen_port))
    server.listen(5)

    print(f"[*] Forwarder listening on {args.listen_ip}:{args.listen_port}")
    print(f"    => EDMS  : {args.edms_ip}:{args.edms_port}")
    print(f"    => Mirror: {args.mirror_ip}:{args.mirror_port}")

    while True:
        client, addr = server.accept()
        th = threading.Thread(
            target=handle_client,
            args=(client, addr, args.edms_ip, args.edms_port, args.mirror_ip, args.mirror_port),
            daemon=True,
        )
        th.start()


if __name__ == "__main__":
    main()
