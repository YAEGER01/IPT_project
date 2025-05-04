def rows_to_dict(cursor, rows):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

def row_to_dict(cursor, row):
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row)) if row else None
def generate_device_token():
    """Generate a unique device token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=64))

def generate_device_fingerprint(request):
    """Generate a device fingerprint based on request headers"""
    fingerprint_data = {
        'user_agent': request.headers.get('User-Agent', ''),
        'accept_language': request.headers.get('Accept-Language', ''),
        'accept_encoding': request.headers.get('Accept-Encoding', ''),
        'accept_charset': request.headers.get('Accept-Charset', ''),
        'ip': request.remote_addr
    }
    fingerprint_str = '|'.join(fingerprint_data.values())
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()
