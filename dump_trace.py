with open("bot_stderr.log", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read().replace("\r", "")
with open("clean_trace.py", "w", encoding="utf-8") as out:
    out.write('TRACE = """\\n' + text + '\\n"""')
