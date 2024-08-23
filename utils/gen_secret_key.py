import secrets

# Private key to firm transaction
def generate_secret_key(length=32):
    return secrets.token_hex(length)


if __name__ == "__main__":
    key = generate_secret_key()
    print("Generated Secret Key:", key)
