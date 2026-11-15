from personal_expenses_app.core.tenant_matching import tenant_match_tokens, tenant_tokens

KOSTKA = "Jose Tellez & Veronica Flores"
STONEFIELD = "Jose Soto & Andrea Zepeda"
OTHERS = ["Yesenia Valenzuela", "Allan C Sanceau"]


def _matches(tenant, others, description):
    tokens, require_all = tenant_match_tokens(tenant, others)
    desc = description.lower()
    hits = [t in desc for t in tokens]
    return bool(tokens) and (all(hits) if require_all else any(hits))


def test_tokens_split_on_spaces_and_ampersand():
    assert tenant_tokens(KOSTKA) == ["jose", "tellez", "veronica", "flores"]
    assert tenant_tokens("Allan C Sanceau") == ["allan", "sanceau"]
    assert tenant_tokens(None) == []


def test_shared_first_name_is_not_used():
    tokens, require_all = tenant_match_tokens(KOSTKA, [STONEFIELD, *OTHERS])
    assert tokens == ["tellez", "veronica", "flores"]
    assert require_all is False


def test_co_tenant_payment_matches_without_shared_first_name():
    # Regression: a payment from the second tenant on the lease was never linked.
    assert _matches(KOSTKA, [STONEFIELD, *OTHERS], "Zelle Payment From Veronica Flores 31085247734")


def test_each_property_keeps_its_own_tenant():
    assert _matches(KOSTKA, [STONEFIELD, *OTHERS], "Zelle Payment From Jose Tellez 123")
    assert _matches(STONEFIELD, [KOSTKA, *OTHERS], "Zelle Payment From Jose Soto Bacu4X4Qeq1T")
    assert not _matches(KOSTKA, [STONEFIELD, *OTHERS], "Zelle Payment From Jose Soto Bacu4X4Qeq1T")
    assert not _matches(STONEFIELD, [KOSTKA, *OTHERS], "Zelle Payment From Veronica Flores 31085247734")


def test_shared_first_name_alone_matches_neither():
    assert not _matches(KOSTKA, [STONEFIELD], "Zelle Payment From Jose 999")
    assert not _matches(STONEFIELD, [KOSTKA], "Zelle Payment From Jose 999")


def test_unique_tenant_matches_any_token():
    assert _matches("Yesenia Valenzuela", [KOSTKA, STONEFIELD], "Zelle Payment From Yesenia Valenzuela 311")


def test_all_tokens_shared_requires_full_name():
    tokens, require_all = tenant_match_tokens("Jose Soto", ["Jose Soto & Andrea Zepeda"])
    assert tokens == ["jose", "soto"] and require_all is True
    assert _matches("Jose Soto", ["Jose Soto & Andrea Zepeda"], "Payment From Jose Soto")
    assert not _matches("Jose Soto", ["Jose Soto & Andrea Zepeda"], "Payment From Jose")
