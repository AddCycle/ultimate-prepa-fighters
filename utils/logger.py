def info(msg: str):
    """Print a info log for the specified side"""
    print(f"[{"SERVER" if __file__ == "server.py" else "CLIENT"}]({__file__}): {msg}")
