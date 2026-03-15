from app.core.api_key_checks import check_gemini_key, check_google_oauth_secret, check_openrouter_key, mask_secret


def test_mask_secret_masks_middle() -> None:
    masked = mask_secret('abcdefghijklmnopqrstuvwxyz')
    assert masked.startswith('abcdef')
    assert masked.endswith('wxyz')
    assert '*' in masked


def test_openrouter_key_format_check() -> None:
    valid = check_openrouter_key('sk-or-v1-abcdefghijklmnopqrstuvwxyz123456')
    invalid = check_openrouter_key('sk-invalid')

    assert valid.present is True
    assert valid.looks_valid is True
    assert invalid.looks_valid is False


def test_gemini_key_format_check() -> None:
    valid = check_gemini_key('AIzaSyAabc1234567890_test-valid-key')
    invalid = check_gemini_key('bad-gemini-key')

    assert valid.present is True
    assert valid.looks_valid is True
    assert invalid.looks_valid is False


def test_google_oauth_secret_format_check() -> None:
    valid = check_google_oauth_secret('GOCSPX-abc1234567890-XYZ')
    invalid = check_google_oauth_secret('bad-secret')

    assert valid.present is True
    assert valid.looks_valid is True
    assert invalid.looks_valid is False
