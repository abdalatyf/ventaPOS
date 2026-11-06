import React, { useState } from 'react';
import { 
  IconBook, 
  IconSearch, 
  IconPrinter, 
  IconCheck, 
  IconAlertCircle, 
  IconInfoCircle,
  IconBuildingStore,
  IconReceipt,
  IconPackage,
  IconChartBar,
  IconCash,
  IconDatabase,
  IconSparkles,
  IconX
} from '@tabler/icons-react';

export default function UserManualModal({ isOpen, onClose }) {
  const [activeChapter, setActiveChapter] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  if (!isOpen) return null;

  const chapters = [
    {
      id: 1,
      title: "1. التشغيل الأول والتفعيل واستعادة النسخ",
      icon: <IconDatabase size={18} className="text-primary flex-shrink-0" />,
      content: (
        <div>
          <h4 className="fw-bold text-primary mb-3">الفصل الأول: التشغيل الأول، التفعيل، واستعادة النسخ الاحتياطية</h4>
          
          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark d-flex align-items-center gap-2">
              <IconSparkles size={18} className="text-warning" />
              1.1 أول تشغيل للبرنامج (وضع التجربة - Demo)
            </h5>
            <p className="text-muted small m-0 leading-relaxed">
              عند فتح البرنامج لأول مرة، يفتح تلقائياً في <strong>وضع العرض التجريبي (Demo Mode)</strong> ببيانات استرشادية واقعية لتجربة كافة الشاشات والقوائم. 
              <br />
              <strong className="text-danger">تنبيه هام:</strong> في وضع التجربة، يتم تجديد البيانات تلقائياً عند كل إعادة تشغيل للبرنامج، لذلك لا تبدأ بإدخال بيانات عملك الحقيقية إلا بعد تفعيل الترخيص الرسمي.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark d-flex align-items-center gap-2">
              <IconCheck size={18} className="text-success" />
              1.2 تفعيل الترخيص الرسمي وتفريغ البيانات
            </h5>
            <ol className="text-muted small m-0 ps-3 leading-relaxed">
              <li className="mb-1">توجه إلى <strong>الإعدادات ⚙️ ⬅️ تبويب الاشتراك</strong> (أو اضغط على زر تفعيل البرنامج في الشاشات الأولى).</li>
              <li className="mb-1">انسخ <strong>بصمة جهازك (Machine ID)</strong> المكونة من 32 رقماً وحرفاً وأرسلها للشركة/المسوق لإصدار كود الترخيص.</li>
              <li className="mb-1">اكتب أو الصق كود التفعيل المكون من 16 حرفاً في خانة الكود ثم اضغط <strong>"تفعيل البرنامج"</strong>.</li>
              <li>عند قبول الكود، يتم مسح بيانات الـ Demo بالكامل وتصفير قاعدة البيانات لبدء نشاطك التجاري الحقيقي بأمان، ويفتح لك البرنامج تلقائياً <strong>معالج التهيئة الأولى (Setup Wizard)</strong> لتحديد اسم فرعك الرئيسي وكلمة مرور المدير.</li>
            </ol>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark d-flex align-items-center gap-2">
              <IconAlertCircle size={18} className="text-azure" />
              1.3 كلمة المرور وحساب المدير وطوارئ الاستعادة
            </h5>
            <p className="text-muted small m-0 leading-relaxed">
              البرنامج مخصص <strong>لمستخدم واحد فقط (صاحب المحل / المدير)</strong> بحساب <code>admin</code>. يمكنك تغيير كلمة المرور في أي وقت من شاشة الإعدادات.
              <br />
              <strong>في حال نسيان كلمة المرور:</strong> يمكنك طلب كود طوارئ لمرة واحدة من الدعم الفني يتيح لك إعادة ضبط كلمة المرور بدون فقدان أي بيانات مسجلة.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark d-flex align-items-center gap-2">
              <IconDatabase size={18} className="text-primary" />
              1.4 استعادة نسخة احتياطية (.sqlite3)
            </h5>
            <p className="text-muted small m-0 leading-relaxed">
              إذا كان لديك ملف نسخة احتياطية سابقة من جهاز آخر: اضغط على زر <strong>"استعادة نسخة احتياطية (.sqlite3)"</strong> المتوفر في شاشة الدخول وشاشة التفعيل والقائمة العلوية. يفحص البرنامج سلامة قاعدة البيانات ويستبدلها بأمان ثم يطلب منك إعادة تسجيل الدخول فوراً.
            </p>
          </div>
        </div>
      )
    },
    {
      id: 2,
      title: "2. تهيئة الفروع والمناديب والموردين والأصناف",
      icon: <IconBuildingStore size={18} className="text-success flex-shrink-0" />,
      content: (
        <div>
          <h4 className="fw-bold text-success mb-3">الفصل الثاني: تهيئة الفروع وإضافة المناديب والموردين والأصناف</h4>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">2.1 إدارة الفروع والمخازن المستقلة</h5>
            <p className="text-muted small m-0 leading-relaxed">
              يدعم البرنامج إدارة عدة فروع أو معارض أو مخازن منفصلة من نفس الجهاز.
              <br />
              <strong>قاعدة استقلال المخازن:</strong> بضاعة ومخزون كل فرع مستقلة تماماً ومحسوبة على حدة. لا يوجد تحويل مباشر لبضاعة بين الفروع (يتم الشراء لكل فرع بفاتورة مستقلة). يمكنك التبديل بين الفروع بضغطة واحدة من القائمة العلوية باختيار <strong>"تغيير الفرع"</strong>.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">2.2 إضافة المناديب ونظام العمولات</h5>
            <p className="text-muted small mb-2 leading-relaxed">
              المناديب في البرنامج يعتمدون 100% على العمولات دون رواتب ثابتة:
            </p>
            <ul className="text-muted small m-0 ps-3 leading-relaxed">
              <li className="mb-1"><strong>عمولة بيع الصنف (المندبة):</strong> مبلغ نقدي ثابت يحدده المدير لكل صنف يباع (مثال: 50 جنيه لكل غسالة، 80 جنيه لغرفة النوم).</li>
              <li><strong>عمولة تحصيل الأقساط:</strong> نسبة مئوية موحدة للمحل (10% افتراضياً) تُحسب على إجمالي المبالغ النقدية المحصلة فعلياً من أقساط المندوب خلال الشهر.</li>
            </ul>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">2.3 إضافة الموردين</h5>
            <p className="text-muted small m-0 leading-relaxed">
              لإضافة تاجر جملة أو مصنع مورد: توجه إلى <strong>الأدوات ⬅️ الموردين</strong>. أدخل اسم المورد، رقم التليفون، والعنوان. يمكنك لاحقاً البحث عن فواتير مشتريات كل مورد ومعرفة إجمالي التوريدات منه.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">2.4 تعريف الأصناف والبضاعة (بدون باركود وبدون سعر بيع ثابت)</h5>
            <ul className="text-muted small m-0 ps-3 leading-relaxed">
              <li className="mb-1"><strong>الاسم التجاري العربي:</strong> هو المعرف الأساسي للصنف (مثال: "طقم حلل جرانيت تركي 10 قطع"، "غسالة شارب 8 كيلو").</li>
              <li className="mb-1"><strong>لا يوجد سعر بيع على الصنف:</strong> المدير يدخل سعر البيع لكل فاتورة بحسب تفاوضه مع العميل أو شروط البيع (كاش أم قسط).</li>
              <li className="mb-1"><strong>رصيد أول المدة:</strong> عند تعريف الصنف لأول مرة، يمكنك إدخال الكمية الموجودة في المخزن حالياً وتاريخ بداية احتسابها.</li>
              <li><strong>المندبة الافتراضية:</strong> تحديد مبلغ المندبة الذي يستحقه المندوب عند بيع هذا الصنف.</li>
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 3,
      title: "3. تسجيل فواتير المبيعات (كاش وقسط) والدفاتر القديمة",
      icon: <IconReceipt size={18} className="text-azure flex-shrink-0" />,
      content: (
        <div>
          <h4 className="fw-bold text-azure mb-3">الفصل الثالث: تسجيل فواتير المبيعات (كاش وقسط) والبيانات السابقة</h4>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">3.1 دورة العمل (تفريغ الدفاتر الورقية)</h5>
            <p className="text-muted small m-0 leading-relaxed">
              المناديب يبيعون للعملاء في الميدان بواسطة الدفاتر الورقية ذات القسائم المكررة. يستلم صاحب المحل / المدير أصول القسائم ويدخلها تباعاً على شاشة <strong>تسجيل فاتورة بيع (POS)</strong> من مكتبه.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">3.2 خطوات تسجيل فاتورة بيع جديدة</h5>
            <ol className="text-muted small m-0 ps-3 leading-relaxed">
              <li className="mb-1">أدخل رقم الفاتورة أو القسيمة من الدفتر الورقي.</li>
              <li className="mb-1">حدد شهر وسنة البيع (يعتمد النظام التاريخ بالشهور مثل <code>2026/08</code>).</li>
              <li className="mb-1">اختر المندوب المسئول عن البيع من القائمة.</li>
              <li className="mb-1">أدخل بيانات العميل (يقترح البرنامج بيانات العميل تلقائياً بمجرد كتابة أول حرفين من اسمه أو هاتفه).</li>
              <li className="mb-1">اختر نوع الدفع: <strong>نقدي (كاش)</strong> أو <strong>تقسيط</strong> (يفتح حقول المقدم وعدد الشهور وقيمة القسط).</li>
              <li className="mb-1">ابحث باسم الصنف وأدخل الكمية وسعر بيع الوحدة لهذه الفاتورة واضغط إضافة.</li>
              <li>اضغط <strong>"حفظ الفاتورة"</strong> (أو اضغط <code>F9</code> من الكيبورد).</li>
            </ol>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">3.3 حساب جدول الأقساط وقاعدة يوم 25</h5>
            <p className="text-muted small m-0 leading-relaxed">
              يطرح البرنامج المقدم من إجمالي الفاتورة لحساب المبلغ المتبقي، ويقسمه على عدد الشهور بالتساوي.
              <br />
              تاريخ استحقاق القسط الأول يبدأ دائماً <strong>في الشهر التالي لتاريخ البيع</strong>. رقم اليوم "25" مطبوع كعرف تجاري لتنسيق الإيصالات، بينما الحساب المحاسبي يعتمد على (الشهر والسنة).
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">3.4 تسجيل البيانات القديمة (فواتير قبل تاريخ الاشتراك)</h5>
            <p className="text-muted small m-0 leading-relaxed">
              عند إدخال تاريخ بيع سابق لتاريخ بدء ترخيصك:
              تتحول الشاشة تلقائياً إلى وضع <strong>"تسجيل البيانات السابقة"</strong>، وتكتفي بكتابة وصف البضاعة كنص حر (مثال: "ثلاجة وغسالة ومفرش") وكتابة إجمالي الفاتورة والمقدم والقسط يدوياً.
              <br />
              <strong className="text-success">الميزة:</strong> لا يخصم هذا الوضع من رصيد فواتير اشتراكك، ولا يؤثر على جرد المخزن الحالي، ولكنه يدرج الأقساط الشهرية في تقارير الأقساط وعمولات التحصيل بدقة.
            </p>
          </div>
        </div>
      )
    },
    {
      id: 4,
      title: "4. طباعة جداول الأقساط وفواتير المشتريات والتقارير",
      icon: <IconPrinter size={18} className="text-dark flex-shrink-0" />,
      content: (
        <div>
          <h4 className="fw-bold text-dark mb-3">الفصل الرابع: طباعة جداول الأقساط وفواتير المشتريات والتقارير</h4>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">4.1 سياسة الطباعة الانتقائية</h5>
            <p className="text-muted small m-0 leading-relaxed">
              حفاظاً على سرعة الإدخال المكتبي، شاشات الإدخال السريع (POS وتسجيل المشتريات) <strong>لا تحتوي على طباعة فورية إجبارية</strong>.
              <br />
              تتم الطباعة المكتبية حصرياً من شاشات البحث والتقارير:
              <br />
              1. <strong>جداول إيصالات الأقساط:</strong> من شاشة بحث الفواتير أو تقرير الأقساط.
              <br />
              2. <strong>فواتير المشتريات ومرتجع الموردين:</strong> من شاشة بحث المشتريات.
              <br />
              3. <strong>التقارير التحليلية والإدارية:</strong> من شاشات التقارير العامة.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">4.2 الأرقام المشرقية في المطبوعات (٠١٢٣٤٥٦٧٨٩)</h5>
            <p className="text-muted small m-0 leading-relaxed">
              تظهر جميع المبالغ والتواريخ في المطبوعات الرسمية بتنسيق الأرقام المشرقية الواضحة (<code>٠١٢٣٤٥٦٧٨٩</code>) وبأعداد صحيحة بدون كسور أو قروش تماشياً مع العرف التجاري في إيصالات الأمانة والأقساط.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">4.3 نافذة الطباعة المتطورة (PrintModal)</h5>
            <p className="text-muted small m-0 leading-relaxed">
              عند الضغط على زر <strong>"طباعة الأقساط" 🖨️</strong>:
              تفحص النافذة حالة الطابعة تلقائياً، وتتيح لك الطباعة على دفعات مجزأة مع خاصية الإيقاف المؤقت وإعادة المحاولة في حال تعثر الطابعة أو نفاد الورق.
            </p>
          </div>
        </div>
      )
    },
    {
      id: 5,
      title: "5. كارت الصنف (المندبة والعجز) والمرتجعات",
      icon: <IconPackage size={18} className="text-warning flex-shrink-0" />,
      content: (
        <div>
          <h4 className="fw-bold text-warning mb-3">الفصل الخامس: كارت الصنف (المندبة والعجز) ومرتجعات البيع والشراء</h4>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">5.1 كارت الصنف التراكمي (Product Ledger)</h5>
            <p className="text-muted small m-0 leading-relaxed">
              من شاشة <strong>الأدوات ⬅️ كارت الصنف</strong>، يمكنك متابعة كشف حساب تفصيلي لأي سلعة:
              (الرصيد الافتتاحي + المشتريات + مرتجع البيع - المبيعات - مرتجع الشراء - العجز = الرصيد الفعلي الحالي).
              النظام يمنع نزول رصيد المخزن تحت الصفر لحماية الجرد الفعلي.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">5.2 تعديل مندبة الصنف مع تغير المواسم والشهور</h5>
            <p className="text-muted small m-0 leading-relaxed">
              يتم تعديل المندبة حصرياً من داخل <strong>كارت الصنف</strong>:
              حدد شهر وسنة بدء سريان المندبة واكتب القيمة الجديدة (مثال: 70 جنيه). يتم تطبيق القيمة الجديدة فقط على الفواتير التالية لهذا التاريخ دون المساس بالحسابات السابقة.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">5.3 تسجيل العجز أو التالف في المعرض</h5>
            <p className="text-muted small m-0 leading-relaxed">
              في حال تلف أو كسر قطعة في المعرض: اضغط على زر <strong>"تسجيل عجز / تسوية مخزنية"</strong> في كارت الصنف، وحدد الكمية وسبب العجز ليتم خصمها محاسبياً دون الحاجة لتسجيل فاتورة بيع وهمية.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">5.4 مرتجعات المبيعات والمشتريات</h5>
            <ul className="text-muted small m-0 ps-3 leading-relaxed">
              <li className="mb-1"><strong>مرتجع المبيعات:</strong> يسجل كفاتورة من نوع <code>مرتجع (RETURN)</code> فتعود البضاعة للمخزن وتخصم قيمتها من مبيعات وعمولة المندوب.</li>
              <li><strong>مرتجع المشتريات:</strong> يسجل من شاشة المشتريات بنوع <code>مرتجع مورد</code> ليخصم من مخزنك ويرد لحساب المورد.</li>
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 6,
      title: "6. المصروفات، الخزنة، التقارير ومرتبات المناديب",
      icon: <IconCash size={18} className="text-danger flex-shrink-0" />,
      content: (
        <div>
          <h4 className="fw-bold text-danger mb-3">الفصل السادس: المصروفات، الخزنة النقدية، والتقارير المالية ومرتبات المناديب</h4>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">6.1 تصنيف المصروفات النثرية والتشغيلية</h5>
            <p className="text-muted small m-0 leading-relaxed">
              سجل كافة مصروفات المحل مقسمة بحسب بنودها (إيجار، كهرباء ومياه، نولون ومشال ونقل، بوفيه ونثريات، صيانة). يتم خصمها تلقائياً من حركة السيولة وصافي الأرباح.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">6.2 حركة الخزنة النقدية (السيولة)</h5>
            <p className="text-muted small m-0 leading-relaxed">
              <strong>الوارد:</strong> المبيعات النقدية + مقدمات التقسيط + الأقساط المحصلة في الشهر الحالي.
              <br />
              <strong>المنصرف:</strong> المصروفات التشغيلية + المدفوع للموردين.
              <br />
              <strong>الرصيد الصافي:</strong> المبلغ النقدي الفعلي المتبقي في درج المحل.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">6.3 حساب مرتبات المناديب</h5>
            <p className="text-muted small mb-2 leading-relaxed">
              من شاشة <strong>التقارير ⬅️ تقرير أداء المناديب</strong>، يحسب البرنامج مرتب المندوب الشهري بالمعادلة التالية:
            </p>
            <div className="p-2 bg-white rounded border border-success text-center fw-bold text-success small mb-2">
              إجمالي مرتب المندوب = مجموع (مندبة كل صنف × الكمية المباعة) + (10% × إجمالي الأقساط المحصلة)
            </div>
            <p className="text-muted small m-0 leading-relaxed">
              يعطيك التقرير كشفاً تفصيلياً جاهزاً للطباعة والتوقيع عليه من المندوب عند الاستلام.
            </p>
          </div>

          <div className="card mb-3 p-3 border-0 bg-light">
            <h5 className="fw-bold text-dark">6.4 التقارير الإدارية والمالية الشاملة</h5>
            <ul className="text-muted small m-0 ps-3 leading-relaxed">
              <li className="mb-1"><strong>تقرير الأرباح والخسائر:</strong> يقارن المبيعات بتكلفة الشراء ويطرح المصروفات والعمولات ليعطيك صافي الربح الحقيقي.</li>
              <li className="mb-1"><strong>تقرير الأقساط المتوقعة:</strong> يعرض التدفقات النقدية المتوقعة لكل الشهور القادمة لمساعدتك في التخطيط.</li>
              <li><strong>تقرير حركة المخزون:</strong> جرد شامل يوضح الأصناف الأكثر مبيعاً والأصناف الراكدة لتنشيط حركتها.</li>
            </ul>
          </div>
        </div>
      )
    }
  ];

  const filteredChapters = searchQuery.trim() === ''
    ? chapters
    : chapters.filter(c => 
        c.title.includes(searchQuery) || 
        c.id.toString() === searchQuery
      );

  const activeChapterData = chapters.find(c => c.id === activeChapter) || chapters[0];

  return (
    <div 
      className="modal modal-blur fade show d-block" 
      tabIndex="-1" 
      role="dialog" 
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.55)', zIndex: 1060 }}
      dir="rtl"
    >
      <div className="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable" role="document">
        <div className="modal-content shadow-lg border-0">
          
          {/* Header */}
          <div className="modal-header bg-light py-2 px-3 border-bottom d-flex justify-content-between align-items-center">
            <div className="d-flex align-items-center gap-2">
              <IconBook size={22} className="text-primary" />
              <h5 className="modal-title fw-bold text-dark m-0">
                دليل تشغيل VentaPOS NextGen (دليل التاجر والمدير)
              </h5>
            </div>
            <button 
              type="button" 
              className="btn-close" 
              onClick={onClose} 
              aria-label="Close" 
            />
          </div>

          {/* Search bar inside modal */}
          <div className="px-3 pt-2 pb-1 bg-white border-bottom">
            <div className="input-icon">
              <span className="input-icon-addon">
                <IconSearch size={18} className="text-muted" />
              </span>
              <input 
                type="text" 
                className="form-control form-control-sm" 
                placeholder="ابحث في فصول وموضوعات دليل الاستخدام..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          {/* Body with Sidebar and Content */}
          <div className="modal-body p-0" style={{ maxHeight: '70vh' }}>
            <div className="row g-0 h-100">
              
              {/* Sidebar chapters */}
              <div className="col-md-4 border-start bg-light p-2" style={{ overflowY: 'auto' }}>
                <div className="list-group list-group-flush rounded border">
                  {filteredChapters.map((chap) => (
                    <button
                      key={chap.id}
                      type="button"
                      className={`list-group-item list-group-item-action d-flex align-items-center gap-2 text-end py-2 px-3 ${
                        activeChapter === chap.id ? 'active fw-bold' : ''
                      }`}
                      onClick={() => setActiveChapter(chap.id)}
                    >
                      {chap.icon}
                      <span className="small">{chap.title}</span>
                    </button>
                  ))}
                  {filteredChapters.length === 0 && (
                    <div className="p-3 text-center text-muted small">
                      لا توجد فصول مطابقة للبحث
                    </div>
                  )}
                </div>

                <div className="mt-3 p-3 bg-white rounded border small text-muted">
                  <div className="fw-bold text-dark mb-1 d-flex align-items-center gap-1">
                    <IconInfoCircle size={16} className="text-primary" />
                    <span>نصيحة ذهبية:</span>
                  </div>
                  <div>
                    احرص على أخذ نسخة احتياطية من قاعدة البيانات أسبوعياً عبر زر <strong>"تصدير نسخة احتياطية"</strong> من شاشة الأدوات واحتفظ بها على فلاشة خارجية.
                  </div>
                </div>
              </div>

              {/* Main Content Area */}
              <div className="col-md-8 p-4 bg-white" style={{ overflowY: 'auto' }}>
                {activeChapterData.content}
              </div>

            </div>
          </div>

          {/* Footer */}
          <div className="modal-footer bg-light py-2 px-3 border-top d-flex justify-content-between align-items-center">
            <div className="text-muted small">
              VentaPOS NextGen v1.0.0 — الدليل التجاري الشامل
            </div>
            <div className="d-flex gap-2">
              <button 
                type="button" 
                className="btn btn-outline-secondary btn-sm px-3" 
                onClick={onClose}
              >
                إغلاق
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
