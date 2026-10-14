#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_API_URL = "https://api.zeptomail.com/v1.1/email"


class InputError(SystemExit):
    pass


def require(env, name):
    value = (env.get(name) or "").strip()
    if not value:
        raise InputError(f"Missing required input: {name}")
    return value


def split_addresses(raw):
    return [part.strip() for part in raw.split(",") if part.strip()]


def recipients(raw, name=""):
    addresses = split_addresses(raw)
    result = []
    for index, address in enumerate(addresses):
        entry = {"address": address}
        if name and index == 0:
            entry["name"] = name
        result.append({"email_address": entry})
    return result


def authorization_header(token):
    token = token.strip()
    if token.lower().startswith("zoho-enczapikey "):
        return token
    return f"Zoho-enczapikey {token}"


def build_payload(env):
    htmlbody = (env.get("ZEPTOMAIL_HTMLBODY") or "").strip()
    textbody = (env.get("ZEPTOMAIL_TEXTBODY") or "").strip()
    if not htmlbody and not textbody:
        raise InputError("Provide htmlbody and/or textbody")

    payload = {
        "from": {"address": require(env, "ZEPTOMAIL_FROM")},
        "to": recipients(
            require(env, "ZEPTOMAIL_TO"),
            (env.get("ZEPTOMAIL_TO_NAME") or "").strip(),
        ),
        "subject": require(env, "ZEPTOMAIL_SUBJECT"),
    }

    from_name = (env.get("ZEPTOMAIL_FROM_NAME") or "").strip()
    if from_name:
        payload["from"]["name"] = from_name
    if htmlbody:
        payload["htmlbody"] = htmlbody
    if textbody:
        payload["textbody"] = textbody

    cc = (env.get("ZEPTOMAIL_CC") or "").strip()
    if cc:
        payload["cc"] = recipients(cc)

    bcc = (env.get("ZEPTOMAIL_BCC") or "").strip()
    if bcc:
        payload["bcc"] = recipients(bcc)

    reply_to = (env.get("ZEPTOMAIL_REPLY_TO") or "").strip()
    if reply_to:
        payload["reply_to"] = [{"address": reply_to}]

    return payload


def api_url(env):
    return (env.get("ZEPTOMAIL_API_URL") or "").strip() or DEFAULT_API_URL


def write_output(path, name, value):
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}<<EOF\n{value}\nEOF\n")


def send_request(url, payload, token, opener=urllib.request.urlopen):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": authorization_header(token),
        },
        method="POST",
    )
    try:
        with opener(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        print(body)
        raise InputError(f"ZeptoMail request failed with HTTP {error.code}") from error


def main(env=None, opener=urllib.request.urlopen):
    env = os.environ if env is None else env
    token = require(env, "ZEPTOMAIL_TOKEN")
    payload = build_payload(env)
    body = send_request(api_url(env), payload, token, opener=opener)
    print(body)
    write_output(env.get("GITHUB_OUTPUT"), "response", body)
    return body


if __name__ == "__main__":
    main()
