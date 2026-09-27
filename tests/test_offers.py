import pytest

import offers


def _jw_payload(offers_list):
    return {"items": [{"offers": offers_list}]}


def test_parse_streaming_offers_rent_and_buy():
    results = _jw_payload(
        [
            {
                "provider_id": 8,
                "retail_price": 3.99,
                "urls": {"standard_web": "https://netflix.example/rent"},
                "monetization_type": "rent",
            },
            {
                "provider_id": 15,
                "retail_price": 12.99,
                "urls": {"standard_web": "https://hulu.example/buy"},
                "monetization_type": "buy",
            },
        ]
    )
    parsed = offers.parse_streaming_offers(results)
    assert parsed == {
        "rent": [
            {
                "provider": "Netflix",
                "price": 3.99,
                "url": "https://netflix.example/rent",
            }
        ],
        "buy": [
            {
                "provider": "Hulu",
                "price": 12.99,
                "url": "https://hulu.example/buy",
            }
        ],
    }


def test_parse_streaming_offers_maps_all_known_providers():
    offer_stubs = [
        (2, "iTunes"),
        (10, "Youtube"),
        (68, "Microsoft"),
        (15, "Hulu"),
        (8, "Netflix"),
        (7, "Vudu"),
        (3, "Google Play"),
    ]
    results = _jw_payload(
        [
            {
                "provider_id": pid,
                "retail_price": 1.0,
                "urls": {"standard_web": "https://example/%s" % pid},
                "monetization_type": "rent",
            }
            for pid, _ in offer_stubs
        ]
    )
    parsed = offers.parse_streaming_offers(results)
    assert [o["provider"] for o in parsed["rent"]] == [name for _, name in offer_stubs]


def test_parse_streaming_offers_skips_unknown_provider():
    results = _jw_payload(
        [
            {
                "provider_id": 9999,
                "retail_price": 1.0,
                "urls": {"standard_web": "https://unknown.example"},
                "monetization_type": "rent",
            },
            {
                "provider_id": 8,
                "retail_price": 2.0,
                "urls": {"standard_web": "https://netflix.example"},
                "monetization_type": "rent",
            },
        ]
    )
    parsed = offers.parse_streaming_offers(results)
    assert len(parsed["rent"]) == 1
    assert parsed["rent"][0]["provider"] == "Netflix"
    assert parsed["buy"] == []


def test_parse_streaming_offers_skips_missing_price_or_url():
    results = _jw_payload(
        [
            {
                "provider_id": 8,
                "urls": {"standard_web": "https://netflix.example"},
                "monetization_type": "rent",
            },
            {
                "provider_id": 15,
                "retail_price": 4.0,
                "urls": {},
                "monetization_type": "buy",
            },
            {
                "provider_id": 7,
                "retail_price": 5.0,
                "urls": {"standard_web": "https://vudu.example"},
                "monetization_type": "buy",
            },
        ]
    )
    parsed = offers.parse_streaming_offers(results)
    assert parsed["rent"] == []
    assert parsed["buy"] == [
        {
            "provider": "Vudu",
            "price": 5.0,
            "url": "https://vudu.example",
        }
    ]


def test_parse_streaming_offers_skips_flatrate_and_unknown_monetization():
    results = _jw_payload(
        [
            {
                "provider_id": 8,
                "retail_price": 0,
                "urls": {"standard_web": "https://netflix.example"},
                "monetization_type": "flatrate",
            },
            {
                "provider_id": 2,
                "retail_price": 3.0,
                "urls": {"standard_web": "https://itunes.example"},
                "monetization_type": "rent",
            },
        ]
    )
    parsed = offers.parse_streaming_offers(results)
    assert parsed["rent"] == [
        {
            "provider": "iTunes",
            "price": 3.0,
            "url": "https://itunes.example",
        }
    ]
    assert parsed["buy"] == []


def test_parse_streaming_offers_empty_offers():
    assert offers.parse_streaming_offers(_jw_payload([])) == {
        "rent": [],
        "buy": [],
    }


def test_parse_streaming_offers_missing_items_raises():
    with pytest.raises((IndexError, KeyError)):
        offers.parse_streaming_offers({"items": []})


def test_apply_main_title_truncation_noop_below_threshold():
    films = [{"title": "A Very Long Movie Title Indeed"}]
    out = offers.apply_main_title_truncation(films)
    assert out is films
    assert films[0]["title"] == "A Very Long Movie Title Indeed"


def test_apply_main_title_truncation_shortens_when_enough_films():
    films = [{"title": "Short"} for _ in range(19)]
    films.append({"title": "ABCDEFGHIJKLMNOP"})  # 16 chars
    offers.apply_main_title_truncation(films)
    assert films[-1]["title"] == "ABCDEFGHIJKLMN..."
    assert films[0]["title"] == "Short"


def test_apply_main_title_truncation_boundary_at_fifteen():
    films = [{"title": "123456789012345"} for _ in range(20)]  # exactly 15
    offers.apply_main_title_truncation(films)
    assert films[0]["title"] == "123456789012345"
    films[0]["title"] = "1234567890123456"  # 16
    offers.apply_main_title_truncation(films)
    assert films[0]["title"] == "12345678901234..."
