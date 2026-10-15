import { test, expect } from '@playwright/test';

// ملاحظة: يُفضل استخدام قاعدة بيانات تجريبية أثناء تشغيل هذه الاختبارات لتجنب إنشاء فواتير حقيقية
// إلا إذا كنت قد هيأت بيئة التطوير لتنظيف نفسها بعد كل عملية.

test.describe('POS Page - الشاشة الرئيسية والميزات الأساسية', () => {
  
  test.beforeEach(async ({ page }) => {
    // محاكاة تسجيل الدخول (يتجاوز صفحة الدخول ويختار الفرع تلقائيا لو كان فرعا واحدا)
    await page.goto('/login');
    
    // انتظار التحويل التلقائي إما للداشبورد أو صفحة الفروع
    await page.waitForURL('**/(select-branch|receipts)', { timeout: 10000 }).catch(() => {});
    
    // إذا توقف في صفحة اختيار الفرع، نضغط على أول فرع
    if (page.url().includes('select-branch')) {
        await page.locator('.card-link').first().click();
        await page.waitForURL('**/receipts', { timeout: 5000 });
    }
    
    // الانتقال لصفحة نقطة البيع
    await page.goto('/pos');
    
    // التأكد من استجابة الصفحة
    await expect(page.getByRole('heading', { name: 'نقطة البيع' })).toBeVisible();
  });

  test('يجب أن تحتوي الصفحة على الحقول الأساسية المحملة', async ({ page }) => {
    // التأكد من وجود خانات شهر وسنة البيع
    const monthInput = page.locator('input[tabindex="1"]');
    await expect(monthInput).toBeVisible();
    
    // التأكد من وجود قائمة المندوب
    const spSelect = page.locator('select[tabindex="3"]');
    await expect(spSelect).toBeVisible();
  });

  test('يجب البحث عن عميل واختياره بشكل صحيح', async ({ page }) => {
    const nameInput = page.locator('input[tabindex="4"]');
    
    // كتابة حرف للبحث
    await nameInput.fill('م');
    
    // انتظار ظهور القائمة المنسدلة (تأخير 50ms في الكود + سرعة الشبكة)
    const suggestionsList = page.locator('.list-group').filter({ hasText: 'م' }).first();
    await expect(suggestionsList).toBeVisible();

    // اختيار أول اقتراح بالضغط على السهم لأسفل ثم Enter
    await nameInput.press('ArrowDown');
    await nameInput.press('Enter');
    
    // التأكد من أن القائمة أغلقت
    await expect(suggestionsList).toBeHidden();
  });

  test('تفعيل تبديل "بيع كاش" يجب أن يخفي بيانات العميل ونظام التقسيط', async ({ page }) => {
    const cashToggle = page.locator('input#cashSaleToggle');
    const nameInput = page.locator('input[tabindex="4"]');
    const downPaymentInput = page.locator('input[tabindex="12"]'); // المقدم
    
    // تأكيد أن الخانات ظاهرة قبل التبديل
    await expect(nameInput).toBeVisible();
    await expect(downPaymentInput).toBeVisible();
    
    // تفعيل بيع كاش
    // Force click since label is what's usually clicked
    await page.locator('label[for="cashSaleToggle"]').click();
    
    // تأكيد اختفاء الخانات
    await expect(nameInput).toBeHidden();
    await expect(downPaymentInput).toBeHidden();
  });
});

test.describe('POS Page - إضافة الأصناف وتجربة عربة التسوق', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForURL('**/(select-branch|receipts)', { timeout: 10000 }).catch(() => {});
    if (page.url().includes('select-branch')) {
        await page.locator('.card-link').first().click();
        await page.waitForURL('**/receipts', { timeout: 5000 });
    }
    await page.goto('/pos');
  });

  test('البحث عن صنف وإضافته للسلة وتأثيره على الإجمالي', async ({ page }) => {
    // 1. بحث عن صنف (نفترض وجود حرف "ب" في قاعدة البيانات)
    const productInput = page.locator('input[tabindex="8"]');
    await productInput.fill('ب');
    
    // انتظار ظهور القائمة واختيار أول صنف
    const productList = page.locator('.list-group button').first();
    await expect(productList).toBeVisible();
    await productList.click();

    // 2. إدخال الكمية والسعر
    const qtyInput = page.locator('input[tabindex="9"]');
    const priceInput = page.locator('input[tabindex="10"]');
    
    await qtyInput.fill('2');
    await priceInput.fill('500'); // الإجمالي سيكون 1000
    
    // الضغط على Enter للإضافة للسلة
    await priceInput.press('Enter');
    
    // 3. التحقق من إضافة الصنف في الجدول
    const tableRow = page.locator('table tbody tr').first();
    await expect(tableRow).toContainText('2'); // الكمية
    await expect(tableRow).toContainText('500'); // السعر
    await expect(tableRow).toContainText('1000'); // الإجمالي
    
    // 4. التحقق من تحديث الإجمالي العام في الأسفل
    const totalDiv = page.locator('text=إجمالي المنتجات').locator('..').locator('.text-dark');
    await expect(totalDiv).toHaveText('1,000');
  });

});

test.describe('POS Page - الحسابات وحفظ الفاتورة', () => {

  test('توزيع نظام القسط المكتوب وعمل الحسابات بشكل صحيح', async ({ page }) => {
    await page.goto('/login');
    await page.waitForURL('**/(select-branch|receipts)', { timeout: 10000 }).catch(() => {});
    if (page.url().includes('select-branch')) {
        await page.locator('.card-link').first().click();
        await page.waitForURL('**/receipts', { timeout: 5000 });
    }
    await page.goto('/pos');
    
    const systemInput = page.locator('input[tabindex="13"]').first(); // نظام القسط
    
    // إدخال نظام قسط (بالأرقام العربية أو الإنجليزية)
    await systemInput.fill('200*3 + 150*2');
    
    // التحقق من أن المجموعات تم تعبئتها تلقائياً
    // الخانة 13 مكررة (لعدد شهور أول مجموعة لأن tabindex يبدأ من 13 هناك أيضاً)
    const group1Count = page.locator('input[tabindex="13"]').nth(1); 
    const group1Amount = page.locator('input[tabindex="14"]').first();
    const group2Count = page.locator('input[tabindex="15"]').first();
    const group2Amount = page.locator('input[tabindex="16"]').first();
    
    // نعتمد على .inputValue() للتحقق من الأرقام
    await expect(group1Count).toHaveValue(/3|٣/);
    await expect(group1Amount).toHaveValue(/200|٢٠٠/);
    await expect(group2Count).toHaveValue(/2|٢/);
    await expect(group2Amount).toHaveValue(/150|١٥٠/);
  });

  test('حفظ الفاتورة الكاش يجب أن ينجح ويظهر رسالة النجاح', async ({ page }) => {
    await page.goto('/login');
    await page.waitForURL('**/(select-branch|receipts)', { timeout: 10000 }).catch(() => {});
    if (page.url().includes('select-branch')) {
        await page.locator('.card-link').first().click();
        await page.waitForURL('**/receipts', { timeout: 5000 });
    }
    await page.goto('/pos');

    // 1. تفعيل الكاش
    await page.locator('label[for="cashSaleToggle"]').click();

    // 2. اختيار صنف
    const productInput = page.locator('input[tabindex="8"]');
    await productInput.fill('ب');
    await page.locator('.list-group button').first().click();
    
    // 3. تعبئة الكمية والسعر وإضافة الصنف
    await page.locator('input[tabindex="9"]').fill('1');
    await page.locator('input[tabindex="10"]').fill('1500');
    // الضغط على Enter للإضافة
    await page.locator('input[tabindex="10"]').press('Enter');

    // التأكد من نزوله في الجدول
    await expect(page.locator('table tbody tr').first()).toContainText('1500');

    // 4. حفظ الفاتورة (ملاحظة: هذا الاختبار سينشئ فاتورة حقيقية)
    page.on('dialog', dialog => {
      console.log('Dialog message:', dialog.message());
      dialog.accept();
    }); 
    
    // انتظار طلب الـ API والتوجيه
    await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/receipts/') && resp.status() === 201, { timeout: 10000 }),
      page.locator('button', { hasText: 'حفظ الفاتورة' }).click(),
    ]);

    // بعد الحفظ الناجح، يجب أن يتم توجيهنا إلى الصفحة الرئيسية
    await expect(page).toHaveURL(/.*\/receipts/);
  });

});
