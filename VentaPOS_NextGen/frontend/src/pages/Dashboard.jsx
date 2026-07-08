import React, { useState, useEffect } from 'react';
import api from '../api';
import { useDefaultDate } from '../hooks/useDefaultDate';

export default function Dashboard() {
  // حالة مؤشرات الأداء والمزامنة
  const [syncQueue, setSyncQueue] = useState({ pending_count: 0 });
  const [kpiData, setKpiData] = useState({
    safe_balance: 0,
    total_sales: 0,
    active_devices: 0
  });

  // جلب البيانات من الـ API (محاكاة أو ربط فعلي)
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // سيتم تفعيل هذه المسارات لاحقاً بناءً على عقد الـ API
        // const response = await api.get('/dashboard/summary/');
        // setKpiData(response.data.kpi);
        // setSyncQueue({ pending_count: response.data.pending_sync });
        
        // بيانات مبدئية للتصميم
        setKpiData({
          safe_balance: 45000,
          total_sales: 128500,
          active_devices: 4
        });
        setSyncQueue({ pending_count: 2 }); // جرب تغيير الرقم لاختبار تغير لون المؤشر
      } catch (error) {
        console.error('خطأ في جلب بيانات الدفتر:', error);
      }
    };

    fetchDashboardData();
  }, []);

  // منطق مؤشر المزامنة وتغير الألوان كما هو محدد في ui_design_tokens
  const getSyncBadgeProps = () => {
    const count = syncQueue.pending_count;
    if (count === 0) {
      return { text: 'الدفتر مُزامن بالكامل', color: '#28a745', bg: '#d4edda' };
    } else if (count <= 5) {
      return { text: `مطلوب مزامنة (${count} فواتير معلقة)`, color: '#ffc107', bg: '#fff3cd' };
    } else {
      return { text: `عاجل: تراكم فواتير معلقة (${count} فاتورة)`, color: '#dc3545', bg: '#f8d7da' };
    }
  };

  const badge = getSyncBadgeProps();

  return (
    <div className="p-6 md:p-8">
      {/* رأس الصفحة */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#212529] mb-1">لوحة متابعة الفرع</h1>
          <p className="text-sm text-[#6c757d]">مرحباً بك، يعرض الدفتر تقرير الأداء الحالي للفرع الرئيسي</p>
        </div>
        
        {/* مؤشر المزامنة */}
        <button 
          onClick={() => alert('جاري تفعيل المزامنة اليدوية...')}
          className="px-4 py-2 rounded-full text-[13px] font-bold shadow-sm transition-transform hover:scale-105"
          style={{ backgroundColor: badge.bg, color: badge.color, border: `1px solid ${badge.color}` }}
        >
          {badge.text}
        </button>
      </div>

      {/* شبكة مؤشرات الأداء KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        
        {/* كارت نقدية الخزنة */}
        <div className="bg-white p-5 rounded-lg shadow-sm border border-[#e5e7eb] border-r-4 border-r-[#28a745]">
          <h3 className="text-sm text-[#6c757d] mb-2 font-semibold">نقدية الخزنة</h3>
          <div className="text-3xl font-black text-[#212529] mb-1" dir="ltr" style={{ textAlign: 'right' }}>
            {kpiData.safe_balance.toLocaleString()}
          </div>
          <p className="text-xs text-[#495057]">النقدية الحالية المتوفرة في درج الخزينة</p>
        </div>

        {/* كارت المبيعات */}
        <div className="bg-white p-5 rounded-lg shadow-sm border border-[#e5e7eb] border-r-4 border-r-[#0f52ba]">
          <h3 className="text-sm text-[#6c757d] mb-2 font-semibold">المبيعات الإجمالية</h3>
          <div className="text-3xl font-black text-[#212529] mb-1" dir="ltr" style={{ textAlign: 'right' }}>
            {kpiData.total_sales.toLocaleString()}
          </div>
          <p className="text-xs text-[#495057]">إجمالي مبيعات الفواتير النقدية والآجلة هذا الشهر</p>
        </div>

        {/* كارت الأجهزة النشطة */}
        <div className="bg-white p-5 rounded-lg shadow-sm border border-[#e5e7eb] border-r-4 border-r-[#6c757d]">
          <h3 className="text-sm text-[#6c757d] mb-2 font-semibold">الأجهزة النشطة</h3>
          <div className="text-3xl font-black text-[#212529] mb-1" dir="ltr" style={{ textAlign: 'right' }}>
            {kpiData.active_devices} أجهزة
          </div>
          <p className="text-xs text-[#495057]">أجهزة المناديب والكاشير النشطة في الشبكة</p>
        </div>

      </div>

      {/* مساحة لإضافة الجداول أو التنبيهات لاحقاً */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-[#e5e7eb] min-h-[300px] flex items-center justify-center">
        <p className="text-[#6c757d]">مساحة مخصصة لقائمة الفواتير الأخيرة أو التنبيهات...</p>
      </div>

    </div>
  );
}
