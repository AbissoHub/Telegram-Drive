import socket
from server.server import app
from utils.config import config


def get_local_ip():
    """Gets the local IPv4 address of the machine."""
    try:
        # Create a dummy connection to discover the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 1))  # Google DNS address, used only to resolve the local IP
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(f"[ERROR] retrieving local IP: {e}")
        return '127.0.0.1'  # Fallback to localhost in case of error


def main():
    ip_address = get_local_ip()
    port = int(config.PORT)  # Use the default port if not present in .env
    print(f"[INFO] Starting server on {ip_address}:{port}")
    app.run(host=ip_address, port=port)


if __name__ == "__main__":
    main()
