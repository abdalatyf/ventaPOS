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

    def test_login_rejects_empty_username_or_password(self):
        """Verify login rejects empty username or password without contacting Supabase."""
        from unittest.mock import patch
        from django.urls import reverse
        from django.test import override_settings

        with override_settings(SUPABASE_KEY="valid-secret-key"):
            with patch('requests.post') as mock_post:
                res1 = self.client.post(reverse('login'), {'username': '', 'password': 'secret'})
                self.assertEqual(res1.status_code, 200)
                self.assertContains(res1, 'يرجى إدخال اسم المستخدم وكلمة المرور')
                self.assertFalse(self.client.session.get('is_logged_in', False))

                res2 = self.client.post(reverse('login'), {'username': 'ahmed', 'password': ''})
                self.assertEqual(res2.status_code, 200)
                self.assertContains(res2, 'يرجى إدخال اسم المستخدم وكلمة المرور')
                self.assertFalse(self.client.session.get('is_logged_in', False))

                mock_post.assert_not_called()

    def test_login_fails_closed_when_supabase_key_missing(self):
        """Verify login fails closed when SUPABASE_KEY is empty."""
        from unittest.mock import patch
        from django.urls import reverse
        from django.test import override_settings

        with override_settings(SUPABASE_KEY=""):
            with patch('requests.post') as mock_post:
                res = self.client.post(reverse('login'), {'username': 'ahmed', 'password': 'secret'})
                self.assertEqual(res.status_code, 200)
                self.assertContains(res, 'SUPABASE_KEY')
                self.assertFalse(self.client.session.get('is_logged_in', False))
                mock_post.assert_not_called()

    def test_login_fails_closed_on_offline_network_error(self):
        """Verify login fails closed when Supabase RPC raises RequestException."""
        from unittest.mock import patch
        import requests
        from django.urls import reverse
        from django.test import override_settings

        with override_settings(SUPABASE_KEY="valid-secret-key"):
            with patch('requests.post', side_effect=requests.RequestException("Network unreachable")):
                res = self.client.post(reverse('login'), {'username': 'ahmed', 'password': 'secret'})
                self.assertEqual(res.status_code, 200)
                self.assertContains(res, 'فشل الاتصال بخادم Supabase')
                self.assertFalse(self.client.session.get('is_logged_in', False))

    def test_login_rejects_invalid_credentials_and_non_200_rpc(self):
        """Verify invalid credentials ({ok: false}) and non-200 HTTP responses are blocked."""
        from unittest.mock import patch, MagicMock
        from django.urls import reverse
        from django.test import override_settings

        with override_settings(SUPABASE_KEY="valid-secret-key"):
            # 1. Invalid credentials
            mock_bad = MagicMock()
            mock_bad.status_code = 200
            mock_bad.json.return_value = {"ok": False}
            with patch('requests.post', return_value=mock_bad):
                res_bad = self.client.post(reverse('login'), {'username': 'ahmed', 'password': 'wrong'})
                self.assertEqual(res_bad.status_code, 200)
                self.assertContains(res_bad, 'اسم المستخدم أو كلمة المرور غير صحيحة')
                self.assertFalse(self.client.session.get('is_logged_in', False))

            # 2. Non-200 HTTP error
            mock_err = MagicMock()
            mock_err.status_code = 500
            mock_err.text = 'Internal Server Error'
            with patch('requests.post', return_value=mock_err):
                res_err = self.client.post(reverse('login'), {'username': 'ahmed', 'password': 'secret'})
                self.assertEqual(res_err.status_code, 200)
                self.assertContains(res_err, 'رفض خادم Supabase التحقق من بيانات الدخول')
                self.assertFalse(self.client.session.get('is_logged_in', False))

    def test_login_success_sets_session_and_stamps_marketeer_id_on_license(self):
        """
        Verify valid Supabase RPC login sets marketeer_username & marketeer_full_name in session,
        shows user badge in sidebar, stamps marketeer_id in public.licenses payload,
        and logout clears session attributes.
        """
        from unittest.mock import patch, MagicMock
        from django.urls import reverse
        from django.test import override_settings

        mock_login_resp = MagicMock()
        mock_login_resp.status_code = 200
        mock_login_resp.json.return_value = {
            "ok": True,
            "username": "ahmed_sales",
            "full_name": "أحمد محمد",
        }

        mock_license_resp = MagicMock()
        mock_license_resp.status_code = 201
        mock_license_resp.text = ""

        with override_settings(SUPABASE_KEY="valid-secret-key", SUPABASE_URL="https://example.supabase.co"):
            with patch('requests.post', return_value=mock_login_resp) as mock_login_post:
                res = self.client.post(reverse('login'), {
                    'username': '  ahmed_sales ',
                    'password': 'StrongPassword!123',
                })
                self.assertEqual(res.status_code, 302)
                self.assertEqual(res.url, reverse('dashboard'))
                self.assertTrue(self.client.session.get('is_logged_in', False))
                self.assertEqual(self.client.session.get('marketeer_username'), 'ahmed_sales')
                self.assertEqual(self.client.session.get('marketeer_full_name'), 'أحمد محمد')

                mock_login_post.assert_called_once()
                self.assertEqual(
                    mock_login_post.call_args.args[0],
                    "https://example.supabase.co/rest/v1/rpc/verify_marketeer_login",
                )
                self.assertEqual(
                    mock_login_post.call_args.kwargs['json'],
                    {"p_username": "ahmed_sales", "p_password": "StrongPassword!123"},
                )

            # Sidebar displays logged-in user badge
            dash_res = self.client.get(reverse('dashboard'))
            self.assertEqual(dash_res.status_code, 200)
            self.assertContains(dash_res, 'أحمد محمد')
            self.assertContains(dash_res, '@ahmed_sales')

            # Issuing a license stamps marketeer_id with the logged-in username
            with patch('requests.post', return_value=mock_license_resp) as mock_lic_post:
                lic_res = self.client.post(reverse('add_license'), {
                    'client': self.client_obj.id,
                    'product_id': 4,
                    'price': 2000,
                    'start_date': '2026-01-01',
                    'notes': 'test attribution',
                })
                self.assertEqual(lic_res.status_code, 302)
                mock_lic_post.assert_called_once()
                payload = mock_lic_post.call_args.kwargs['json']
                self.assertEqual(payload['marketeer_id'], 'ahmed_sales')

            # Logout clears session user info
            out_res = self.client.get(reverse('logout'))
            self.assertEqual(out_res.status_code, 302)
            self.assertFalse(self.client.session.get('is_logged_in', False))
            self.assertIsNone(self.client.session.get('marketeer_username'))
            self.assertIsNone(self.client.session.get('marketeer_full_name'))

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


