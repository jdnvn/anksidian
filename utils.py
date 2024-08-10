import uuid
import base64
import hashlib

def guid():
    random_uuid = uuid.uuid4()
    uuid_bytes = random_uuid.bytes
    guid = base64.urlsafe_b64encode(uuid_bytes).decode('ascii')
    guid = guid[:10]
    return guid

def checksum(input_string):
    # Encode the input string to bytes
    input_bytes = input_string.encode('utf-8')
    
    # Calculate the checksum
    sha1 = hashlib.sha1()
    sha1.update(input_bytes)
    checksum = sha1.hexdigest()
    checksum_int = int(checksum, 16)
    
    # Ensure the checksum is 10 digits long
    checksum_10_digits = checksum_int % (10**10)
    checksum_str = f"{checksum_10_digits}0"
    checksum_10_digits_int = int(checksum_str)

    return checksum_10_digits_int


# TODO: Implement this wrapper
# def sqlite_connection(function):
#     def wrapper(*args, **kwargs):
#         conn = get_connection()
#         result = function(conn, *args, **kwargs)
#         conn.close()
#         return result
#     return wrapper

