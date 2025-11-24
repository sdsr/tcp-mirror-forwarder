import socket
import threading
import argparse


def forward_connection(client_sock, client_addr, dests):
    print(f"[+] Client connected from {client_addr}")

    # Connect to all destinations
    dest_socks = []
    for ip, port in dests:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            dest_socks.append(s)
            print(f"  -> Connected to {ip}:{port}")
        except Exception as e:
            print(f"  !! Failed to connect {ip}:{port} - {e}")

    try:
        while True:
            data = client_sock.recv(4096)
            if not data:
                break

            for s in list(dest_socks):
                try:
                    s.sendall(data)
                except Exception as e:
                    print(f"  !! Failed to send to {s.getpeername()}: {e}")
                    dest_socks.remove(s)
                    s.close()

            if not dest_socks:
                print("  !! No targets left; stopping forwarding.")
                break

    finally:
        print(f"[-] Client disconnected {client_addr}")
        client_sock.close()
        for s in dest_socks:
            s.close()


def main():
    parser = argparse.ArgumentParser(description="TCP Mirror Forwarder")

    parser.add_argument("--listen-ip", default="0.0.0.0")
    parser.add_argument("--listen-port", type=int, default=8501,
                        help="Port to receive data from ED")

    parser.add_argument("--edms-ip", default="192.168.10.23")
    parser.add_argument("--edms-port", type=int, default=8500)

    parser.add_argument("--mypc-ip", default="192.168.10.6")
    parser.add_argument("--mypc-port", type=int, default=8500)

    args = parser.parse_args()

    dests = [
        (args.edms_ip, args.edms_port),
        (args.mypc_ip, args.mypc_port)
    ]

    # Prepare listener
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.listen_ip, args.listen_port))
    server.listen(5)

    print(f"[*] Forwarder listening on {args.listen_ip}:{args.listen_port}")
    print(f"    -> EDMS: {args.edms_ip}:{args.edms_port}")
    print(f"    -> MYPC: {args.mypc_ip}:{args.mypc_port}")

    while True:
        client, addr = server.accept()
        th = threading.Thread(
            target=forward_connection,
            args=(client, addr, dests),
            daemon=True
        )
        th.start()


if __name__ == "__main__":
    main()
