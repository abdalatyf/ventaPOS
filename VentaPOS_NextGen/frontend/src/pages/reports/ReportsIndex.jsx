import React from 'react';
import { Link } from 'react-router-dom';
import { 
  IconDashboard, 
  IconUsers, 
  IconPackage, 
  IconChartPie, 
  IconCash, 
  IconCalendarEvent 
} from '@tabler/icons-react';

export default function ReportsIndex() {
  const reports = [
    {
      title: "لوحة تقارير الأداء",
      desc: "متابعة المؤشرات المالية وحالة المخزون والمبيعات",
      icon: <IconDashboard size={40} className="text-primary mb-3" />,
      link: "/reports/dashboard",
      color: "blue"
    },
    {
      title: "الأرباح والخسائر بالتفصيل",
      desc: "تفصيل الإيرادات، التكاليف، وصافي الربح للمبيعات",
      icon: <IconChartPie size={40} className="text-purple mb-3" />,
      link: "/reports/profit-and-loss",
      color: "purple"
    },
    {
      title: "حركة وجرد المخازن",
      desc: "متابعة أرصدة البضاعة والمشتريات والمبيعات",
      icon: <IconPackage size={40} className="text-orange mb-3" />,
      link: "/reports/inventory",
      color: "orange"
    },
    {
      title: "عمولات وأداء المناديب",
      desc: "تقييم المبيعات واحتساب رواتب الموظفين والمناديب",
      icon: <IconUsers size={40} className="text-teal mb-3" />,
      link: "/reports/salesperson",
      color: "teal"
    },
    {
      title: "حركة درج الخزينة",
      desc: "تفاصيل فواتير الكاش والمقدمات والتحصيلات",
      icon: <IconCash size={40} className="text-green mb-3" />,
      link: "/reports/cash-drawer",
      color: "green"
    },
    {
      title: "تقرير الأقساط والتحصيلات",
      desc: "متابعة وجدولة الأقساط المستحقة وتجميعاتها",
      icon: <IconCalendarEvent size={40} className="text-red mb-3" />,
      link: "/reports/installments",
      color: "red"
    }
  ];

  return (
    <div className="page-wrapper" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div className="page-header d-print-none flex-shrink-0">
        <div className="container-fluid">
          <div className="row g-2 align-items-center">
            <div className="col">
              <h2 className="page-title">قسم التقارير والتحليلات</h2>
              <div className="text-muted mt-1">اختر التقرير الذي تود استعراضه</div>
            </div>
          </div>
        </div>
      </div>

      <div className="page-body flex-grow-1 overflow-auto">
        <div className="container-fluid py-4">
          <div className="row row-deck row-cards">
            {reports.map((report, idx) => (
              <div className="col-sm-6 col-lg-4" key={idx}>
                <Link to={report.link} className="card card-link card-link-pop text-decoration-none">
                  <div className={`card-status-top bg-${report.color}`}></div>
                  <div className="card-body text-center py-5">
                    {report.icon}
                    <h3 className="card-title mb-2 text-dark">{report.title}</h3>
                    <div className="text-muted">{report.desc}</div>
                  </div>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
