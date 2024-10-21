from server.server import app


def main():
    app.run(host='192.168.1.249', port=5000)


if __name__ == "__main__":
    main()
