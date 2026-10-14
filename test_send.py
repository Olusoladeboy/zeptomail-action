#!/usr/bin/env python3
import io
import json
import os
import tempfile
import unittest
import urllib.error
from unittest.mock import Mock

import send


def base_env(**overrides):
    env = {
        "ZEPTOMAIL_TOKEN": "test-token",
        "ZEPTOMAIL_FROM": "noreply@example.com",
        "ZEPTOMAIL_TO": "dev@example.com",
        "ZEPTOMAIL_SUBJECT": "Deploy finished",
        "ZEPTOMAIL_HTMLBODY": "<p>ok</p>",
    }
    env.update(overrides)
    return env


class FakeResponse:
    def __init__(self, body, status=200):
        self._body = body.encode("utf-8")
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class SendTests(unittest.TestCase):
    def test_require_missing(self):
        with self.assertRaises(send.InputError):
            send.require({}, "ZEPTOMAIL_TOKEN")

    def test_split_addresses(self):
        self.assertEqual(
            send.split_addresses(" a@x.com, b@x.com , "),
            ["a@x.com", "b@x.com"],
        )

    def test_recipients_name_only_on_first(self):
        self.assertEqual(
            send.recipients("a@x.com,b@x.com", "Dev"),
            [
                {"email_address": {"address": "a@x.com", "name": "Dev"}},
                {"email_address": {"address": "b@x.com"}},
            ],
        )

    def test_authorization_adds_prefix(self):
        self.assertEqual(
            send.authorization_header("abc"),
            "Zoho-enczapikey abc",
        )

    def test_authorization_keeps_existing_prefix(self):
        self.assertEqual(
            send.authorization_header("Zoho-enczapikey abc"),
            "Zoho-enczapikey abc",
        )

    def test_build_payload_requires_body(self):
        env = base_env()
        env.pop("ZEPTOMAIL_HTMLBODY")
        with self.assertRaises(send.InputError):
            send.build_payload(env)

    def test_build_payload_optional_fields(self):
        payload = send.build_payload(
            base_env(
                ZEPTOMAIL_FROM_NAME="Bot",
                ZEPTOMAIL_TO_NAME="Dev",
                ZEPTOMAIL_TEXTBODY="ok",
                ZEPTOMAIL_CC="cc@example.com",
                ZEPTOMAIL_BCC="bcc@example.com",
                ZEPTOMAIL_REPLY_TO="reply@example.com",
            )
        )
        self.assertEqual(payload["from"]["name"], "Bot")
        self.assertEqual(payload["to"][0]["email_address"]["name"], "Dev")
        self.assertEqual(payload["textbody"], "ok")
        self.assertEqual(payload["cc"][0]["email_address"]["address"], "cc@example.com")
        self.assertEqual(payload["bcc"][0]["email_address"]["address"], "bcc@example.com")
        self.assertEqual(payload["reply_to"][0]["address"], "reply@example.com")

    def test_default_api_url(self):
        self.assertEqual(send.api_url({}), send.DEFAULT_API_URL)

    def test_main_posts_payload_and_writes_output(self):
        opener = Mock(return_value=FakeResponse('{"ok":true}'))
        with tempfile.TemporaryDirectory(dir=os.path.dirname(__file__)) as tmp:
            output_path = os.path.join(tmp, "github_output")
            env = base_env(GITHUB_OUTPUT=output_path)
            body = send.main(env=env, opener=opener)
            with open(output_path, encoding="utf-8") as handle:
                output = handle.read()

        self.assertEqual(body, '{"ok":true}')
        opener.assert_called_once()
        request = opener.call_args[0][0]
        self.assertEqual(request.full_url, send.DEFAULT_API_URL)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.headers["Authorization"], "Zoho-enczapikey test-token")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["to"][0]["email_address"]["address"], "dev@example.com")
        self.assertIn('response<<EOF\n{"ok":true}\nEOF', output)

    def test_main_fails_on_http_error(self):
        error = urllib.error.HTTPError(
            send.DEFAULT_API_URL,
            401,
            "Unauthorized",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"bad token"}'),
        )
        opener = Mock(side_effect=error)
        with self.assertRaises(send.InputError) as raised:
            send.main(env=base_env(), opener=opener)
        self.assertIn("401", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
