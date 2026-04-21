"""Run the mock gpsd server.

Usage:
    python -m gpsd_mock [--port PORT] [--interval SECONDS]
"""

import argparse

from gpsd_mock.server import MockGpsdServer


def main():
    parser = argparse.ArgumentParser(description="Mock gpsd server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=2947, help="TCP port")
    parser.add_argument(
        "--interval", type=float, default=1.0, help="Seconds between TPV messages"
    )
    parser.add_argument(
        "--speed", type=float, default=5.0, help="Speed in m/s (~11 mph)"
    )
    args = parser.parse_args()

    server = MockGpsdServer(
        host=args.host,
        port=args.port,
        speed_mps=args.speed,
        interval=args.interval,
    )
    addr = server.server_address
    print(f"Mock gpsd serving on {addr[0]}:{addr[1]}")
    print(f"  Center: 45.5104, -122.68365 (Portland State University)")
    print(f"  Radius: 0.5 mi, Speed: {args.speed} m/s, Interval: {args.interval}s")
    print("  Connect with: gpspipe -w localhost")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
