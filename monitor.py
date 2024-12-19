import psutil
import socket
import json
from tabulate import tabulate
import time
import argparse

def fetch_network_activity(filter_ip=None, filter_port=None, only_active=False):
    connections = psutil.net_connections(kind='inet')
    activity = []

    for conn in connections:
        laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
        raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
        status = conn.status
        proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"

        if only_active and status != "ESTABLISHED":
            continue
        if filter_ip and (filter_ip not in (conn.laddr.ip if conn.laddr else '', conn.raddr.ip if conn.raddr else '')):
            continue
        if filter_port and (filter_port not in (conn.laddr.port if conn.laddr else '', conn.raddr.port if conn.raddr else '')):
            continue

        activity.append({
            "Local Address": laddr,
            "Remote Address": raddr,
            "Status": status,
            "Protocol": proto
        })
    
    return activity

def display_activity(activity, output_format="table"):
    if not activity:
        print("\nNo network activity found matching the criteria.\n")
        return

    if output_format == "table":
        headers = ["Local Address", "Remote Address", "Status", "Protocol"]
        rows = [[a[header] for header in headers] for a in activity]
        print("\nCurrent Network Activity:")
        print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))
    elif output_format == "json":
        print("\nCurrent Network Activity in JSON Format:")
        print(json.dumps(activity, indent=4))

def log_activity(activity, log_file):
    with open(log_file, "a") as f:
        for entry in activity:
            f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network Activity Monitor")
    parser.add_argument("--filter-ip", type=str, help="Filter connections by IP address")
    parser.add_argument("--filter-port", type=int, help="Filter connections by port")
    parser.add_argument("--only-active", action="store_true", help="Show only active connections")
    parser.add_argument("--output-format", type=str, choices=["table", "json"], default="table", help="Output format")
    parser.add_argument("--log-file", type=str, help="Log activity to a file")
    parser.add_argument("--periodic", type=int, help="Periodically check network activity (in seconds)")

    args = parser.parse_args()

    if args.periodic:
        print(f"Monitoring network activity every {args.periodic} seconds... Press Ctrl+C to stop.")
        try:
            previous_activity = []
            while True:
                current_activity = fetch_network_activity(args.filter_ip, args.filter_port, args.only_active)
                if current_activity != previous_activity:
                    display_activity(current_activity, args.output_format)
                    if args.log_file:
                        log_activity(current_activity, args.log_file)
                previous_activity = current_activity
                time.sleep(args.periodic)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    else:
        activity = fetch_network_activity(args.filter_ip, args.filter_port, args.only_active)
        display_activity(activity, args.output_format)
        if args.log_file:
            log_activity(activity, args.log_file)
