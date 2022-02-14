def create_credential(username, password):
    Result = {
        "CredentialPair": {
            "Username": username,
            "Password": password,
        }
    }
    return Result


def update_nested_dict(in_dict, key, value):
    for k, v in in_dict.items():
        if key == k:
            in_dict[k] = value
        elif isinstance(v, dict):
            update_nested_dict(v, key, value)
        elif isinstance(v, list):
            for o in v:
                if isinstance(o, dict):
                    update_nested_dict(o, key, value)


def remove_nested_dict(in_dict):
    out_dict = {}
    if isinstance(in_dict, dict):
        for k in in_dict:
            if in_dict[k]:
                out_dict[k] = remove_nested_dict(in_dict[k])
        return out_dict
    else:
        return in_dict
