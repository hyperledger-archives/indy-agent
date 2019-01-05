import base64


def serialize_bytes_json(data: bytes) -> str:
    data_b64_encoded = base64.b64encode(data)
    data_b64_encoded_str = data_b64_encoded.decode('utf-8')
    return data_b64_encoded_str


def deserialize_bytes_json(b64_encoded: bytes) -> str:
    b64_decoded = base64.b64decode(b64_encoded)
    b64_decoded_str = b64_decoded.encode('utf-8')
    return b64_decoded_str


def str_to_bytes(data: str) -> bytes:
    return str.encode(data)


def bytes_to_str(data: bytes) -> str:
    return data.decode('utf-8')
