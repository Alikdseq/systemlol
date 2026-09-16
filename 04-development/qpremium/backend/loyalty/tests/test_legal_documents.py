from django.test import SimpleTestCase

from legal.loader import CONSENT_VERSION, consent_text, public_catalog


class LegalDocumentsTests(SimpleTestCase):
    def test_consent_version_v2(self):
        texts = consent_text()
        for key in ("PROGRAM_RULES", "PERSONAL_DATA", "ADVERTISING"):
            self.assertEqual(texts[key]["version"], CONSENT_VERSION)
            self.assertGreater(len(texts[key]["text"]), 400)

    def test_privacy_policy_covers_152(self):
        text = public_catalog()["privacy"]["text"]
        for needle in (
            "152-ФЗ",
            "трансгранич",
            "Telegram",
            "Роскомнадзор",
            "локализац",
            "шифр",
            "отзыв",
        ):
            self.assertIn(needle.lower(), text.lower(), needle)

    def test_advertising_covers_38(self):
        text = public_catalog()["advertising"]["text"]
        for needle in (
            "38-ФЗ",
            "ООО «ШИК»",
            "ooo_shik@internet.ru",
            "СМС",
            "отказ",
            "реклам",
        ):
            self.assertIn(needle.lower(), text.lower(), needle)

    def test_pd_consent_excludes_advertising(self):
        text = public_catalog()["personal-data"]["text"]
        self.assertIn("не покрывается", text)
        self.assertIn("152-ФЗ", text)

    def test_public_api(self):
        listing = self.client.get("/api/v1/legal")
        self.assertEqual(listing.status_code, 200)
        slugs = {d["slug"] for d in listing.json()["documents"]}
        self.assertEqual(slugs, {"privacy", "personal-data", "advertising", "program-rules"})
        for slug in slugs:
            r = self.client.get(f"/api/v1/legal/{slug}")
            self.assertEqual(r.status_code, 200, slug)
            self.assertTrue(r.json()["text"].strip())

    def test_unknown_slug_404(self):
        r = self.client.get("/api/v1/legal/unknown")
        self.assertEqual(r.status_code, 404)
