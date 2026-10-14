# zeptomail-action

GitHub Action that sends a transactional email through [Zoho ZeptoMail](https://www.zoho.com/zeptomail/).

Published as [`olusoladeboy/zeptomail-action`](https://github.com/olusoladeboy/zeptomail-action).

## Usage

```yaml
- name: Send email
  uses: olusoladeboy/zeptomail-action@v1
  with:
    token: ${{ secrets.ZEPTOMAIL_TOKEN }}
    from: noreply@example.com
    from_name: Deploy Bot
    to: team@example.com
    subject: Deploy finished
    htmlbody: '<p>The deploy completed.</p>'
```

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `token` | yes | ZeptoMail Send Mail Token. With or without the `Zoho-enczapikey` prefix. |
| `from` | yes | Verified sender address |
| `from_name` | no | Sender display name |
| `to` | yes | Recipients, comma-separated |
| `to_name` | no | Display name for the first recipient |
| `subject` | yes | Subject |
| `htmlbody` | no | HTML body (required if `textbody` is empty) |
| `textbody` | no | Plain-text body |
| `cc` | no | CC addresses, comma-separated |
| `bcc` | no | BCC addresses, comma-separated |
| `reply_to` | no | Reply-To address |
| `api_url` | no | Defaults to `https://api.zeptomail.com/v1.1/email` |

## Output

- `response` — raw JSON from ZeptoMail

## Tests

```bash
python3 test_send.py
```

The tests mock the ZeptoMail HTTP call and do not send real mail.

```
