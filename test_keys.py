from stellar_sdk import Keypair

secret = "SCREHS7BFLL2L22DL6LGFFQ2UAITICUMOBE5RVTOEPVDRWFDQLNOQWG6"
pub = "GAHO2LQHLZHYRRUE4CNT7QHWFDXJWK322XPUWO6RSFGB3FMI4H67OH5J"

kp = Keypair.from_secret(secret)
print(f"Secret Public: {kp.public_key}")
print(f"Env Public: {pub}")
print(f"Match: {kp.public_key == pub}")
