"""
Django Test Suite for LicenseManager app.
"""
from django.test import TestCase
from datetime import date
from .utils.crypto import LicenseGenerator
from .models import Client, License


class LicenseManagerModelAndCryptoTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name="محل تجريبي",
            phone="01012345678",
            machine_id="5410972688ec8bb4e16d99723ecdbf7a",
            store_name="الأمانة للأجهزة"
        )

    def test_license_auto_generation_on_save(self):
        """
        Verify that creating a License instance automatically generates
        a valid 16-character license code.
        """
        lic = License.objects.create(
            client=self.client_obj,
            product_id=4,  # Standard 1-Year
            price=2500,
            start_date=date(2026, 1, 1)
        )
        self.assertTrue(lic.generated_code)
        self.assertEqual(len(lic.generated_code), 19)

        # Validate generated code
        res = LicenseGenerator.validate(lic.generated_code, self.client_obj.machine_id)
        self.assertTrue(res["valid"])
        self.assertEqual(res["product_id"], 4)
        self.assertEqual(res["start_year"], 2026)
        self.assertEqual(res["start_month"], 1)

    def test_emergency_recovery_code(self):
        """
        Verify emergency code properties and validation.
        """
        lic = License.objects.create(
            client=self.client_obj,
            product_id=16,
            price=0,
            start_date=date(2026, 1, 1)
        )
        self.assertTrue(lic.is_emergency_code)
        res = LicenseGenerator.validate(lic.generated_code, self.client_obj.machine_id)
        self.assertTrue(res["valid"])
        self.assertEqual(res["product_id"], 16)

    def test_client_form_machine_id_validation(self):
        """
        Verify that ClientForm strictly validates 32-character hexadecimal machine IDs.
        """
        from .forms import ClientForm

        # 1. Valid 32-hex lowercase
        form1 = ClientForm(data={
            'name': 'عميل سليم',
            'phone': '01011112222',
            'store_name': 'محل 1',
            'machine_id': 'aabbccddeeff00112233445566778899',
            'is_banned': False
        })
        self.assertTrue(form1.is_valid(), form1.errors)
        self.assertEqual(form1.cleaned_data['machine_id'], 'aabbccddeeff00112233445566778899')

        # 2. Valid uppercase 32-hex (should be normalized to lowercase)
        form2 = ClientForm(data={
            'name': 'عميل حروف كبيرة',
            'phone': '01011112222',
            'store_name': 'محل 2',
            'machine_id': 'AABBCCDDEEFF00112233445566778898',
            'is_banned': False
        })
        self.assertTrue(form2.is_valid(), form2.errors)
        self.assertEqual(form2.cleaned_data['machine_id'], 'aabbccddeeff00112233445566778898')

        # 3. Invalid legacy format (e.g. DISK-5822-S9J1)
        form3 = ClientForm(data={
            'name': 'عميل قديم',
            'phone': '01011112222',
            'machine_id': 'DISK-5822-S9J1',
            'is_banned': False
        })
        self.assertFalse(form3.is_valid())
        self.assertIn('machine_id', form3.errors)

        # 4. Invalid non-hex characters
        form4 = ClientForm(data={
            'name': 'عميل غير هيكس',
            'phone': '01011112222',
            'machine_id': '5410972688ec8bb4e16d99723ecdbfzz',
            'is_banned': False
        })
        self.assertFalse(form4.is_valid())
        self.assertIn('machine_id', form4.errors)

    def test_license_form_excludes_cloud_products(self):
        """
        Verify that deprecated cloud products (8 and 9) are removed from LicenseForm choices.
        """
        from .forms import LicenseForm
        form = LicenseForm()
        choice_keys = [c[0] for c in form.fields['product_id'].choices]
        self.assertNotIn(8, choice_keys)
        self.assertNotIn(9, choice_keys)
        self.assertIn(4, choice_keys)
        self.assertIn(16, choice_keys)


class LicenseManagerViewTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name="عميل اختبار",
            phone="01099998888",
            machine_id="5410972688ec8bb4e16d99723ecdbf7a",
            store_name="معرض النور"
        )
        self.banned_client = Client.objects.create(
            name="عميل محظور",
            phone="01055554444",
            machine_id="11223344556677889900aabbccddeeff",
            store_name="المعرض المحظور",
            is_banned=True
        )

    def _login_session(self):
        session = self.client.session
        session['is_logged_in'] = True
        session.save()

    def test_banned_client_cannot_issue_license(self):
        """
        Verify that add_license_view rejects issuing licenses to clients with is_banned=True.
        """
        from django.urls import reverse
        self._login_session()
        response = self.client.post(reverse('add_license'), {
            'client': self.banned_client.id,
            'product_id': 4,
            'price': 2000,
            'start_date': '2026-01-01',
            'notes': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'محظور من إصدار الرخص')
        self.assertEqual(License.objects.filter(client=self.banned_client).count(), 0)

    def test_fail_closed_when_supabase_key_empty(self):
        """
        Verify that when SUPABASE_KEY is empty, key generation is blocked (fail-closed).
        """
        from django.urls import reverse
        from django.test import override_settings
        self._login_session()

        with override_settings(SUPABASE_KEY=""):
            response = self.client.post(reverse('add_license'), {
                'client': self.client_obj.id,
                'product_id': 4,
                'price': 2000,
                'start_date': '2026-01-01',
                'notes': ''
            })
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'مفتاح الربط السحابي (SUPABASE_KEY) غير معين')
            self.assertEqual(License.objects.count(), 0)

    def test_fail_closed_when_supabase_network_error(self):
        """
        Verify that network timeouts / connection errors abort key generation.
        """
        from unittest.mock import patch
        import requests
        from django.urls import reverse
        from django.test import override_settings
        self._login_session()

        with override_settings(SUPABASE_KEY="fake-secret-key"):
            with patch('requests.post', side_effect=requests.RequestException("Connection refused")):
                response = self.client.post(reverse('add_license'), {
                    'client': self.client_obj.id,
                    'product_id': 4,
                    'price': 2000,
                    'start_date': '2026-01-01',
                    'notes': ''
                })
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'فشل الاتصال بخادم التراخيص السحابي')
                self.assertEqual(License.objects.count(), 0)

    def test_fail_closed_when_supabase_rejects_with_error_status(self):
        """
        Verify that Supabase returning HTTP 400 or 500 aborts key generation.
        """
        from unittest.mock import patch, MagicMock
        from django.urls import reverse
        from django.test import override_settings
        self._login_session()

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = '{"message": "RLS policy violation"}'

        with override_settings(SUPABASE_KEY="fake-secret-key"):
            with patch('requests.post', return_value=mock_resp):
                response = self.client.post(reverse('add_license'), {
                    'client': self.client_obj.id,
                    'product_id': 4,
                    'price': 2000,
                    'start_date': '2026-01-01',
                    'notes': ''
                })
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'رفض خادم Supabase تسجيل الترخيص')
                self.assertEqual(License.objects.count(), 0)

    def test_successful_license_issue_with_supabase(self):
        """
        Verify that when Supabase returns HTTP 201 Created, license is saved
        and user is redirected to license_success.
        """
        from unittest.mock import patch, MagicMock
        from django.urls import reverse
        from django.test import override_settings
        self._login_session()

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.text = ''

        with override_settings(SUPABASE_KEY="valid-secret-key"):
            with patch('requests.post', return_value=mock_resp) as mock_post:
                response = self.client.post(reverse('add_license'), {
                    'client': self.client_obj.id,
                    'product_id': 4,
                    'price': 2000,
                    'start_date': '2026-01-01',
                    'notes': 'ملاحظة فنية'
                })
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/licenses/success/'))

                # Verify license was saved
                self.assertEqual(License.objects.count(), 1)
                lic = License.objects.first()
                self.assertEqual(lic.client, self.client_obj)
                self.assertEqual(lic.product_id, 4)
                self.assertTrue(lic.generated_code)

                # Verify payload sent to Supabase
                mock_post.assert_called_once()
                call_kwargs = mock_post.call_args.kwargs
                payload = call_kwargs['json']
                self.assertEqual(payload['machine_id'], self.client_obj.machine_id)
                self.assertEqual(payload['client_name'], self.client_obj.name)
                self.assertEqual(payload['product_id'], 4)
                self.assertEqual(payload['license_code'], lic.generated_code)

    def test_login_fails_closed_when_master_password_empty(self):
        """Verify login fails closed when MASTER_PASSWORD is empty (never falls back to '123')."""
        from django.urls import reverse
        from django.test import override_settings

        with override_settings(MASTER_PASSWORD=""):
            res_default = self.client.post(reverse('login'), {'password': '123'})
            self.assertEqual(res_default.status_code, 200)
            self.assertContains(res_default, 'VENTA_LICENSE_MASTER_PASSWORD')
            self.assertFalse(self.client.session.get('is_logged_in', False))

            res_empty = self.client.post(reverse('login'), {'password': ''})
            self.assertEqual(res_empty.status_code, 200)
            self.assertFalse(self.client.session.get('is_logged_in', False))

    def test_login_succeeds_with_configured_master_password_and_rejects_wrong(self):
        """Verify constant-time login succeeds only with the exact configured MASTER_PASSWORD."""
        from django.urls import reverse
        from django.test import override_settings

        with override_settings(MASTER_PASSWORD="StrongAdminPass!99"):
            bad_res = self.client.post(reverse('login'), {'password': '123'})
            self.assertEqual(bad_res.status_code, 200)
            self.assertContains(bad_res, 'كلمة المرور غير صحيحة')
            self.assertFalse(self.client.session.get('is_logged_in', False))

            ok_res = self.client.post(reverse('login'), {'password': 'StrongAdminPass!99'})
            self.assertEqual(ok_res.status_code, 302)
            self.assertEqual(ok_res.url, reverse('dashboard'))
            self.assertTrue(self.client.session.get('is_logged_in', False))

    def test_issue_product_15_topup_5000_vs_product_16_recovery_mocked_supabase(self):
        """
        Verify add_license_view separates product_id=15 (5000-invoice top-up) from
        product_id=16 (emergency password recovery) with external Supabase calls mocked.
        """
        from unittest.mock import patch, MagicMock
        from django.urls import reverse
        from django.test import override_settings
        self._login_session()

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.text = ''

        with override_settings(SUPABASE_KEY="valid-secret-key"):
            with patch('requests.post', return_value=mock_resp) as mock_post:
                # 1. Mint product_id=15 (Top-up +5000 invoices)
                r15 = self.client.post(reverse('add_license'), {
                    'client': self.client_obj.id,
                    'product_id': 15,
                    'price': 500,
                    'start_date': '2026-02-01',
                    'notes': '5000 topup'
                })
                self.assertEqual(r15.status_code, 302)

                # 2. Mint product_id=16 (Emergency password recovery)
                r16 = self.client.post(reverse('add_license'), {
                    'client': self.client_obj.id,
                    'product_id': 16,
                    'price': 0,
                    'start_date': '2026-02-01',
                    'notes': 'emergency reset'
                })
                self.assertEqual(r16.status_code, 302)

                self.assertEqual(mock_post.call_count, 2)
                p15 = mock_post.call_args_list[0].kwargs['json']
                p16 = mock_post.call_args_list[1].kwargs['json']
                self.assertEqual(p15['product_id'], 15)
                self.assertIn('5000', p15['product_name'])
                self.assertIsNone(p15['expiry_date'])
                self.assertEqual(p16['product_id'], 16)
                self.assertIsNone(p16['expiry_date'])

                lic15 = License.objects.get(product_id=15)
                lic16 = License.objects.get(product_id=16)
                self.assertTrue(lic15.is_invoice_based)
                self.assertFalse(lic15.is_emergency_code)
                self.assertTrue(lic16.is_emergency_code)
                self.assertFalse(lic16.is_invoice_based)

                val15 = LicenseGenerator.validate(lic15.generated_code, self.client_obj.machine_id)
                val16 = LicenseGenerator.validate(lic16.generated_code, self.client_obj.machine_id)
                self.assertTrue(val15['valid'])
                self.assertEqual(val15['product_id'], 15)
                self.assertTrue(val16['valid'])
                self.assertEqual(val16['product_id'], 16)


