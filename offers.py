"""Pure helpers for JustWatch offer parsing and main-page title display.

Kept free of Flask / JustWatch imports so unit tests run under CI without the
2018 app dependency pin set (and without network).
"""

STREAMING_PROVIDERS = {
    2: "iTunes",
    10: "Youtube",
    68: "Microsoft",
    15: "Hulu",
    8: "Netflix",
    7: "Vudu",
    3: "Google Play",
}


def parse_streaming_offers(results):
    """Turn a JustWatch ``search_for_item`` payload into rent/buy offer lists.

    Mirrors historical ``app.streaming`` behavior: unknown provider ids, missing
    fields, and monetization types other than ``rent``/``buy`` are skipped.
    An empty or missing ``items`` list raises ``IndexError`` / ``KeyError`` as
    before (callers historically assumed at least one hit).
    """
    dct = {"rent": [], "buy": []}
    for item in results["items"][0]["offers"]:
        try:
            offer = {
                "provider": STREAMING_PROVIDERS[item["provider_id"]],
                "price": item["retail_price"],
                "url": item["urls"]["standard_web"],
            }
            dct[item["monetization_type"]].append(offer)
        except Exception:
            continue
    return dct


def apply_main_title_truncation(films, min_count=20, max_len=15):
    """Apply main-page title shortening when there are enough films.

    Historical rule from ``app.main``: only when ``len(films) >= 20``, titles
    longer than 15 characters become the first 14 characters plus ``...``.
    Mutates film dicts in place and returns the same list.
    """
    if len(films) >= min_count:
        for item in films:
            if len(item["title"]) > max_len:
                item["title"] = item["title"][: max_len - 1] + "..."
    return films
