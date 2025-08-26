 

status_str = "在看"

def get_status(status_str):
    if status_str == "看过":
        return "COLLECT"
    elif status_str == "在看":
        return "DO"
    elif status_str == "想看":
        return "WISH"
    else:
        return None

status = get_status(status_str)
print(status)
