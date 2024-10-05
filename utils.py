# NOTE: Those functions are rewrite of JavaScript code found on www.cast2tv.io.
# Even it's rewritten, still it should be attributed to InstantBits Inc

import re

BASE36 = list("0123456789abcdefghijklmnopqrstuvwxyz")

def fromBase36(value):
    chars = value.lower()
    decoded = 0
    for char in chars:
        idx = BASE36.index(char)
        if idx > -1:
            decoded = (decoded * len(BASE36)) + idx
    return decoded

def intToIp(value):
    if value is None:
        return None
    if isinstance(value, str):
        result = re.search(r"\d+", value)
        if not result:
            return None
        value = int(result.group(0))
    return '.'.join([str((value >> (8 * i)) & 0xff) for i in range(3, -1, -1)])

PRIVATE_SUBNETS = [
    {"start": 3232235520, "end": 3232301055},  # 192.168.0.0-192.168.255.255
    {"start": 167772160, "end": 184549375},    # 10.0.0.0-10.255.255.255
    {"start": 2886729728, "end": 2887778303}   # 172.16.0.0-172.31.255.255
]
minIp = 16777216  # 1.0.0.0

def codeToIps(code, port=None):
    p = fromBase36(port) if port else 30001
    if p < 30000:
        p += 30000
    codeInt = fromBase36(code)
    subnetShortcuts = [subnet['start'] for subnet in PRIVATE_SUBNETS]
    ips = []
    if codeInt < minIp:
        for subnet_start in subnetShortcuts:
            ip = intToIp(codeInt + subnet_start)
            ips.append(f"{ip}:{p}")
    else:
        ip = intToIp(codeInt)
        ips.append(f"{ip}:{p}")
    return ips
