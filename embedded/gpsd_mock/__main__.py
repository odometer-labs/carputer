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
        "--speed", type=float, default=8.0, help="Speed in m/s (~18 mph city driving)"
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
    print(f"  Route: City blocks around PSU / South Park Blocks")
    print(f"  Speed: {args.speed} m/s (~{args.speed * 2.237:.0f} mph), Interval: {args.interval}s")
    print("  Connect with: gpspipe -w localhost")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
