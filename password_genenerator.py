import hashlib
import secrets

def generate_scrypt_hash(password, n=16384, r=8, p=1):s
"""
    Generate a scrypt hash with custom parameters.

    :param password: The password to hash (string)
    :param n: CPU/memory cost parameter (integer, e.g., 16384)
    :param r: Block size parameter (integer, e.g., 8)
    :param p: Parallelization parameter (integer, e.g., 1)
    :return: The scrypt hash as a formatted string
    """
    # Generate a secure random salt
salt = secrets.token_urlsafe(16)
    
    # Use the scrypt hashing algorithm
hashed_password = hashlib.scrypt(
        password.encode(),
        salt=salt.encode(),
        n=n,
        r=r,
        p=p,
        maxmem=64 * 1024 * 1024  # Adjust max memory (e.g., 64 MiB)
    )
    
    # Format the output
return f"scrypt:{n}:{r}:{p}${salt}${hashed_password.hex()}"
if __name__ == "__main__":
    password = input("Enter your password: ")
    hashed_password = generate_scrypt_hash(password)
    print(f"Formatted Hashed Password: {hashed_password}")