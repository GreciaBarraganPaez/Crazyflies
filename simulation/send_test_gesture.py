#!/usr/bin/env python3
"""Send one test gesture from Windows to the Ubuntu UDP bridge (no AI needed)."""
import argparse
import socket

GESTURES = ('one', 'peace', 'three', 'ok', 'palm', 'fist')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host', required=True, help='Ubuntu WSL IPv4 address (hostname -I)')
    p.add_argument('--port', type=int, default=5055)
    p.add_argument('--gesture', required=True, choices=GESTURES)
    args = p.parse_args()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(args.gesture.encode('ascii'), (args.host, args.port))
    print(f'Sent {args.gesture} -> {args.host}:{args.port} (UDP has no delivery confirmation)')


if __name__ == '__main__':
    main()
