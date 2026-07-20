# VentaPOS NextGen REST API Contract

هذا المستند يمثل العقد البرمجي الموحد (API Contract) للنسخة المطورة **VentaPOS NextGen Rebuild** متوافقاً مع مواصفات **OpenAPI 3.1.0**.

---

## 🔒 1. السياسة الأمنية والتحقق من الهوية (Authentication & Security)

تدعم البوابة خيارين للتحقق من الصلاحيات حسب نوع العميل المتصل:
1. **التحقق المستند إلى رمز الوصول (JWT Bearer Token):** ويستخدم في واجهات الويب (React) ومستخدمي السحابة (Cloud Viewers) عبر ترويسة الطلب:
   `Authorization: Bearer <JWT_TOKEN>`
2. **التحقق المستند إلى معرف الجهاز ورمز الشركة (Machine & Company Headers):** ويستخدم لمزامنة البيانات بين الأجهزة المحلية (Desktop/Mobile) والخادم المركزي عبر الترويسات التالية:
   - `X-Machine-ID`: المعرف الفريد للجهاز المحلي (Hardware UUID).
   - `X-Company-Code`: الرمز التعريفي للشركة المكون من 4 أرقام لربط الأجهزة بالخزينة الرئيسية.

---

## 🌐 2. خوادم النظام (Server Configurations)

تم إعداد النظام للعمل على بيئات متعددة مع دعم الأنفاق الآمنة للتطوير المحلي:

*   **الخادم الرئيسي (Production Server):**
    `https://api.ventapos.com/v1`
*   **خادم التطوير والمزامنة المحلي (Local Tunneling Server - Ngrok):**
    `https://jargonal-colourationally-buddy.ngrok-free.dev/api/v1` (يُستخدم لربط نقاط البيع المحلية وتخطي جدران الحماية).

---

## 🔁 3. طبقة ترجمة الحقول (SQLite-to-Django Translation Layer)

لتجنب حدوث أي فقدان في البيانات (Data Dropping) أثناء عمليات المزامنة والسحب (Pull/Push) بين قاعدة البيانات المحلية (SQLite) وقاعدة البيانات المركزية (PostgreSQL)، يقوم النظام بترجمة الحقول تلقائياً كالتالي:

### أ) جدول المنتجات / البضاعة (Inventory Items Mapping)
| Django Backend Field (PostgreSQL) | Local SQLite Field | Description |
| :--- | :--- | :--- |
| `local_id` | `id` | المعرف الفريد للمنتج محلياً |
| `quantity` | `initial_quantity` | رصيد المخزون الافتتاحي |
| `purchase_price` | `initial_purchase_price` | سعر تكلفة شراء المنتج |
| `salesperson_commission_amount` | `initial_commission_amount` | قيمة عمولة المندوب |
| `created_at_local` | `created_at` | تاريخ إضافة المنتج محلياً |

### ب) جدول الفواتير (Receipts Mapping)
| Django Backend Field (PostgreSQL) | Local SQLite Field | Description |
| :--- | :--- | :--- |
| `local_id` | `id` | الرقم المسلسل للفاتورة محلياً |
| `local_branch_id` | `branch_id` | معرف الفرع المنسوب للفاتورة |
| `local_salesperson_id` | `salesperson_id` | معرف مندوب المبيعات |
| `created_at_local` | `created_at` | تاريخ ووقت إنشاء الفاتورة محلياً |
| `customer_phone` | `phone_number` | رقم هاتف العميل |
| `customer_address` | `address` | عنوان العميل |
| `customer_area` | `area` | منطقة أو حي العميل |

---

## 💳 4. قاعدة الأقساط وفاتورة الاستحقاق (25th Billing Rule)

يلتزم النظام بالمعايير التالية لإدارة عمليات البيع بالتقسيط ومنع التلاعب:
*   **تسمية المفاتيح (Normalization Key Names):** يجب استخدام كلمة `"installments"` بدلاً من `"payments"` أو `"installment_payments"`.
*   **تاريخ الاستحقاق (Due Date Key):** داخل مصفوفة الأقساط، يجب استخدام الحقل `"payment_date"` بدلاً من `"date"` أو `"due_date"`.
*   **قاعدة الـ 25 من كل شهر:** يتم توليد تواريخ الأقساط تلقائياً لتبدأ من يوم **25 في الشهر التالي** لتاريخ البيع. يُحظر تعديل هذه التواريخ يدوياً وتعتبر المخالفة محاولة تلاعب بالبيانات.
*   **منع التكرار (Collision Prevention):** يتم الاعتماد كلياً على الهاش التشفيري الفريد الفردي للفاتورة `receipt_hash` لضمان عدم حدوث تداخل بين الفواتير الواردة من أجهزة مختلفة.

---

## 💬 5. لغة السوق المهنية المبسطة للواجهات والأخطاء (RTL & Arabic Language Policy)

تمت صياغة رسائل الأخطاء وتوصيف الكيانات بلغة سوق مهنية ومبسطة قريبة لتجّار السوق المصري دون ابتذال، مع استخدام المسميات التالية:
*   **العميل** (وليس الزبون أو المشتري).
*   **البضاعة / المنتج** (بدلاً من المادة أو الصنف).
*   **الخزنة / المالية** (بدلاً من الصندوق أو النقدية الصافية).
*   **الفاتورة** (بدلاً من الإيصال أو المستند المعاملاتي).
*   **الدفتر** (بدلاً من الأرشيف أو النظام المالي).
*   **المندوب** (بدلاً من الموظف أو الكاشير).

---

## 📋 6. عقد مواصفات OpenAPI 3.1.0 (JSON Specification)

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "VentaPOS NextGen REST API",
    "version": "1.0.0",
    "description": "واجهة برمجة التطبيقات المطورة لنظام VentaPOS لإدارة المبيعات والمخازن والمزامنة السحابية."
  },
  "servers": [
    {
      "url": "https://api.ventapos.com/v1",
      "description": "خادم السحابة الرئيسي (الإنتاج)"
    },
    {
      "url": "https://jargonal-colourationally-buddy.ngrok-free.dev/api/v1",
      "description": "نفق التطوير والمزامنة المحلي (Ngrok)"
    }
  ],
  "security": [
    {
      "JWTAuth": []
    }
  ],
  "paths": {
    "/api/v1/auth/viewer/": {
      "post": {
        "summary": "توثيق مستخدم السحابة (Cloud Viewer)",
        "description": "يسمح هذا المسار لمستخدمي السحابة أو الملاك بالتحقق من بيانات الدخول للوصول إلى تفاصيل الدفتر والمبيعات.",
        "security": [],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["company_code", "username", "password_hash"],
                "properties": {
                  "company_code": {
                    "type": "string",
                    "maxLength": 4,
                    "description": "رمز الشركة المكون من 4 أرقام.",
                    "example": "1234"
                  },
                  "username": {
                    "type": "string",
                    "description": "اسم المستخدم المسجل.",
                    "example": "ahmed_manager"
                  },
                  "password_hash": {
                    "type": "string",
                    "description": "الهاش التشفيري لكلمة المرور الخاصة بالمستخدم.",
                    "example": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "تم التحقق بنجاح وإرجاع بيانات الاتصال بالخزنة الرئيسية.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": {
                      "type": "string",
                      "example": "success"
                    },
                    "master_machine_id": {
                      "type": "string",
                      "example": "mac-uuid-777-888"
                    },
                    "user": {
                      "type": "object",
                      "properties": {
                        "username": { "type": "string", "example": "1234-ahmed_manager" },
                        "role": { "type": "string", "example": "VIEWER" },
                        "local_id": { "type": "integer", "example": 1 }
                      }
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "بيانات الدخول ناقصة أو غير صحيحة.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "بيانات الدخول ناقصة، يرجى كتابة رمز الشركة واسم المستخدم كاملاً."
                }
              }
            }
          },
          "401": {
            "description": "خطأ في كلمة المرور أو اسم المستخدم.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "غير مصرح بالدخول، يرجى التحقق من اسم المستخدم أو كلمة المرور الخاصة بالخزنة."
                }
              }
            }
          },
          "403": {
            "description": "اشتراك السحابة معطل أو منتهي الصلاحية.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "الاشتراك السحابي للشركة انتهى أو معطل، يرجى التجديد لتتمكن من الدخول."
                }
              }
            }
          },
          "404": {
            "description": "رمز الشركة غير موجود.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "رمز الشركة المكتوب غير مسجل في الدفتر، يرجى التحقق من الرقم."
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sync/push/": {
      "post": {
        "summary": "إرسال ومزامنة الفواتير والبيانات (Sync Push Ingestion)",
        "description": "يسمح للأجهزة المحلية بدفع الفواتير والأقساط والمصروفات والمنتجات وتعديلاتها دفعة واحدة بطريقة ذرية (Atomic Transaction) لضمان اتساق البيانات بالخادم.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["machine_id", "payload"],
                "properties": {
                  "machine_id": {
                    "type": "string",
                    "description": "المعرف الفريد للجهاز المحلي الراسل للبيانات."
                  },
                  "payload": {
                    "type": "object",
                    "properties": {
                      "company_settings": {
                        "type": "object",
                        "properties": {
                          "name": { "type": "string" },
                          "description": { "type": "string" },
                          "phone1": { "type": "string" },
                          "phone2": { "type": "string" },
                          "footer_text": { "type": "string" }
                        }
                      },
                      "branches": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "id": { "type": "integer" },
                            "name": { "type": "string" }
                          }
                        }
                      },
                      "salespeople": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "id": { "type": "integer" },
                            "branch_id": { "type": "integer" },
                            "name": { "type": "string" }
                          }
                        }
                      },
                      "inventory": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "id": { "type": "integer" },
                            "branch_id": { "type": "integer" },
                            "name": { "type": "string" },
                            "quantity": { "type": "integer" },
                            "purchase_price": { "type": "string" },
                            "commission": { "type": "string" },
                            "created_at": { "type": "string", "format": "date-time" }
                          }
                        }
                      },
                      "receipts": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "required": ["receipt_hash", "id", "receipt_number", "total_amount", "is_cash_sale"],
                          "properties": {
                            "receipt_hash": {
                              "type": "string",
                              "description": "الهاش الأمني الفريد للفاتورة لمنع التكرار والتصادم."
                            },
                            "id": { "type": "integer" },
                            "receipt_number": { "type": "integer" },
                            "branch_id": { "type": "integer" },
                            "salesperson_id": { "type": "integer" },
                            "customer_name": { "type": "string" },
                            "phone_number": { "type": "string" },
                            "address": { "type": "string" },
                            "area": { "type": "string" },
                            "total_amount": { "type": "string" },
                            "down_payment": { "type": "string" },
                            "installment_system": { "type": "string" },
                            "sale_year": { "type": "integer" },
                            "sale_month": { "type": "integer" },
                            "is_cash_sale": { "type": "boolean" },
                            "created_at": { "type": "string", "format": "date-time" },
                            "items": {
                              "type": "array",
                              "items": {
                                "type": "object",
                                "properties": {
                                  "product_id": { "type": "integer" },
                                  "product_name": { "type": "string" },
                                  "quantity": { "type": "integer" },
                                  "price": { "type": "string" }
                                }
                              }
                            },
                            "installments": {
                              "type": "array",
                              "description": "قائمة الأقساط المستحقة للفاتورة.",
                              "items": {
                                "type": "object",
                                "required": ["payment_date", "amount"],
                                "properties": {
                                  "payment_date": {
                                    "type": "string",
                                    "format": "date",
                                    "description": "تاريخ استحقاق القسط (يجب أن يخضع لقاعدة الـ 25)."
                                  },
                                  "amount": {
                                    "type": "string",
                                    "description": "قيمة القسط المالي."
                                  }
                                }
                              }
                            }
                          }
                        }
                      },
                      "expenses": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "id": { "type": "integer" },
                            "branch_id": { "type": "integer" },
                            "amount": { "type": "string" },
                            "description": { "type": "string" },
                            "expense_year": { "type": "integer" },
                            "expense_month": { "type": "integer" },
                            "created_at": { "type": "string", "format": "date-time" }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "تمت مزامنة البضاعة والفواتير وحفظها بالدفتر بنجاح.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "message": { "type": "string", "example": "تم مزامنة البيانات وحفظ الفواتير بالدفتر بنجاح." },
                    "receipts_processed": { "type": "integer", "example": 5 }
                  }
                }
              }
            }
          },
          "400": {
            "description": "خطأ في بنية البيانات المرسلة أو فشل التحقق من الحقول الموحدة (Data Validation Mismatch).",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "بيانات الفاتورة غير مطابقة أو ناقصة، يرجى مراجعة الدفتر والتأكد من حقول الأقساط وتواريخها."
                }
              }
            }
          },
          "403": {
            "description": "رخصة الجهاز منتهية الصلاحية أو غير نشطة.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "الاشتراك السحابي انتهى، يرجى التجديد لتتمكن من مزامنة الفواتير."
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sync/pull/": {
      "get": {
        "summary": "سحب تحديثات البيانات (Sync Pull View - GET)",
        "description": "جلب تحديثات البضائع، الفروع، المناديب، الفواتير، والمصاريف التي تم إضافتها بعد تاريخ آخر مزامنة للفرع أو المندوب.",
        "parameters": [
          {
            "name": "machine_id",
            "in": "query",
            "required": true,
            "schema": { "type": "string" }
          },
          {
            "name": "last_sync",
            "in": "query",
            "required": true,
            "schema": { "type": "string", "format": "date-time" },
            "description": "تاريخ آخر مزامنة تم سحبها محلياً."
          },
          {
            "name": "company_code",
            "in": "query",
            "required": false,
            "schema": { "type": "string" }
          },
          {
            "name": "role",
            "in": "query",
            "required": false,
            "schema": { "type": "string" }
          },
          {
            "name": "salesperson_id",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          }
        ],
        "responses": {
          "200": {
            "description": "قائمة تحديثات الكيانات التي طرأت على السيرفر مع حقول SQLite المترجمة.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/SyncPullResponse" }
              }
            }
          },
          "403": {
            "description": "غير مصرح للجهاز بالسحب لانتهاء الترخيص.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "الاشتراك السحابي غير فعال، يرجى مراجعة إدارة الترخيص بالشركة."
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "سحب تحديثات البيانات (Sync Pull View - POST)",
        "description": "مطابق لطريقة GET ولكن يدعم إرسال المتغيرات الأمنية داخل جسم الطلب (Body) لتفادي ظهور رموز التعريف في الروابط.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["machine_id", "last_sync"],
                "properties": {
                  "machine_id": { "type": "string" },
                  "last_sync": { "type": "string", "format": "date-time" },
                  "company_code": { "type": "string" },
                  "role": { "type": "string" },
                  "salesperson_id": { "type": "integer" }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "قائمة تحديثات الكيانات الناجحة.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/SyncPullResponse" }
              }
            }
          },
          "400": {
            "description": "بيانات الطلب خاطئة.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" }
              }
            }
          }
        }
      }
    },
    "/api/v1/sync/confirm-receipts/": {
      "post": {
        "summary": "تأكيد استلام فواتير الهواتف المحمولة",
        "description": "يقوم الجهاز الرئيسي (Master POS) بتأكيد استلام فواتير المندوبين وتثبيتها بالخزنة لإلغاء حالة الانتظار (is_confirmed = true).",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["machine_id", "receipt_hashes"],
                "properties": {
                  "machine_id": { "type": "string" },
                  "receipt_hashes": {
                    "type": "array",
                    "items": { "type": "string" },
                    "description": "قائمة الهاش للفواتير المراد تأكيدها."
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "تم تأكيد الفواتير بنجاح.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "updated_count": { "type": "integer", "example": 3 }
                  }
                }
              }
            }
          },
          "403": {
            "description": "غير مصرح للجهاز الرئيسي.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "غير مصرح للجهاز بتأكيد الحساب المالي، يرجى مراجعة إدارة الخزنة."
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/products/": {
      "get": {
        "summary": "عرض بضاعة الفرع (Products List)",
        "description": "جلب قائمة بضاعة الفرع الحالية مع حساب كمية رصيد المخزون الفعلي بناءً على معادلة الزمن التراجعي.",
        "parameters": [
          {
            "name": "branch_id",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          },
          {
            "name": "month",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          },
          {
            "name": "year",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          }
        ],
        "responses": {
          "200": {
            "description": "تم جلب قائمة البضائع المتاحة بالخزنة.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": { "$ref": "#/components/schemas/ProductSchema" }
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "إضافة أو تعديل بضاعة (Add/Modify Product)",
        "description": "إدخال بضاعة جديدة للدفتر أو تعديل أسعار التكلفة وعمولات المناديب.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/ProductSchema" }
            }
          }
        },
        "responses": {
          "201": {
            "description": "تم تسجيل البضاعة بالدفتر بنجاح.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "product": { "$ref": "#/components/schemas/ProductSchema" }
                  }
                }
              }
            }
          },
          "400": {
            "description": "خطأ في بيانات الصنف.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "فشل إضافة الصنف، يرجى كتابة اسم البضاعة وسعر التكلفة بشكل صحيح."
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/receipts/": {
      "get": {
        "summary": "استعراض فواتير المبيعات (Search & Filter Receipts)",
        "description": "قائمة بفواتير المبيعات الجارية والأقساط المستحقة والمحصلة مع فلترة حسب الفرع أو المندوب أو العميل.",
        "parameters": [
          {
            "name": "branch_id",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          },
          {
            "name": "salesperson_id",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          },
          {
            "name": "is_cash_sale",
            "in": "query",
            "required": false,
            "schema": { "type": "boolean" }
          }
        ],
        "responses": {
          "200": {
            "description": "قائمة الفواتير المطلوبة.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": { "$ref": "#/components/schemas/ReceiptSchema" }
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "إصدار فاتورة بيع جديدة (Create Sale Receipt)",
        "description": "تسجيل عملية بيع نقدية أو بالتقسيط بالخزنة. ملاحظة: هذه العملية تخصم من رصيد الفواتير المتاحة للرخصة النشطة (Invoices Balance).",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/ReceiptSchema" }
            }
          }
        },
        "responses": {
          "201": {
            "description": "تم إصدار الفاتورة وحساب الأقساط وفق قاعدة الـ 25 بنجاح.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "receipt_number": { "type": "integer", "example": 1022 },
                    "receipt_hash": { "type": "string", "example": "a4f89d09c6238b1f2095f87b8d009211c47dfd6e3c3b03698a96d13a6df91278" }
                  }
                }
              }
            }
          },
          "400": {
            "description": "البيانات غير صالحة أو فشل التحقق من سلامتها.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "حسابات الفاتورة خاطئة، القيمة الإجمالية لا تطابق أسعار البضاعة المباعة."
                }
              }
            }
          },
          "403": {
            "description": "فشل إصدار الفاتورة بسبب انتهاء باقة الترخيص أو نفاد الرصيد المتاح من الفواتير.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "لا يمكن طباعة أو إصدار الفاتورة، رصيد الفواتير المسموح به للرخصة قد نفد. يرجى الشحن أولاً."
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/expenses/": {
      "get": {
        "summary": "استعراض مصروفات الفرع (Branch Expenses)",
        "description": "جلب المصاريف الجارية والعمومية المسجلة بالخزينة لفرع معين.",
        "parameters": [
          {
            "name": "branch_id",
            "in": "query",
            "required": true,
            "schema": { "type": "integer" }
          },
          {
            "name": "year",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          },
          {
            "name": "month",
            "in": "query",
            "required": false,
            "schema": { "type": "integer" }
          }
        ],
        "responses": {
          "200": {
            "description": "قائمة المصروفات الخاصة بالفرع.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": { "$ref": "#/components/schemas/ExpenseSchema" }
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "تسجيل بند مصروفات (Track Branch Expense)",
        "description": "إضافة بند منصرف مالي جديد لخزينة الفرع مع ربطه بالدفتر السنوي والشهري.",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/ExpenseSchema" }
            }
          }
        },
        "responses": {
          "201": {
            "description": "تم تدوين المصروف بالدفتر المالي للفرع بنجاح.",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string", "example": "success" },
                    "expense": { "$ref": "#/components/schemas/ExpenseSchema" }
                  }
                }
              }
            }
          },
          "400": {
            "description": "المبلغ المالي أو الوصف المسجل غير صحيح.",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/ErrorResponse" },
                "example": {
                  "status": "error",
                  "message": "فشل تدوين المصروف، يرجى التأكد من كتابة قيمة بند المصروفات وتحديد الفرع."
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "ErrorResponse": {
        "type": "object",
        "required": ["status", "message"],
        "properties": {
          "status": {
            "type": "string",
            "example": "error"
          },
          "message": {
            "type": "string",
            "description": "رسالة الخطأ الموجهة للمستخدم بلغة سوق مبسطة لعرضها مباشرة بالواجهة.",
            "example": "بيانات الفاتورة غير مطابقة أو ناقصة، يرجى مراجعة الدفتر والتأكد من حقول الأقساط."
          }
        }
      },
      "ProductSchema": {
        "type": "object",
        "required": ["name", "branch_id", "initial_quantity", "initial_purchase_price"],
        "properties": {
          "id": { "type": "integer", "description": "المعرف الرئيسي بالدفتر المركزي" },
          "name": { "type": "string", "description": "اسم البضاعة / المنتج" },
          "branch_id": { "type": "integer", "description": "الفرع المنسوب له البضاعة" },
          "initial_quantity": { "type": "integer", "description": "المخزون الافتتاحي للفرع" },
          "initial_purchase_price": { "type": "integer", "description": "سعر شراء وتكلفة القطعة بالخزنة" },
          "initial_commission_amount": { "type": "integer", "description": "عمولة المندوب الافتتاحية للمبيعات" },
          "initial_month": { "type": "integer", "example": 6 },
          "initial_year": { "type": "integer", "example": 2026 },
          "current_stock": { "type": "integer", "readOnly": true, "description": "رصيد المخزون الفعلي بناءً على الحساب التراجعي" }
        }
      },
      "ReceiptSchema": {
        "type": "object",
        "required": ["branch_id", "total_amount", "is_cash_sale", "receipt_hash", "items"],
        "properties": {
          "receipt_hash": { "type": "string", "description": "التوقيع التشفيري للفاتورة لمنع تداخل الحسابات المالية" },
          "receipt_number": { "type": "integer", "description": "رقم مسلسل الفاتورة محلياً بالفرع" },
          "branch_id": { "type": "integer", "description": "الفرع الصادر منه الفاتورة" },
          "salesperson_id": { "type": "integer", "nullable": true },
          "customer_name": { "type": "string", "description": "اسم العميل المسجل بالفاتورة" },
          "customer_phone": { "type": "string", "nullable": true },
          "customer_address": { "type": "string", "nullable": true },
          "customer_area": { "type": "string", "nullable": true },
          "total_amount": { "type": "integer", "description": "إجمالي القيمة المالية للفاتورة" },
          "down_payment": { "type": "integer", "description": "مقدم الدفع النقدي في حالة البيع بالقسط" },
          "sale_month": { "type": "integer", "example": 6 },
          "sale_year": { "type": "integer", "example": 2026 },
          "is_cash_sale": { "type": "boolean", "description": "هل المعاملة نقدية بالكامل (نقدية) أم بالأقساط" },
          "items": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["inventory_item_id", "quantity", "unit_price"],
              "properties": {
                "inventory_item_id": { "type": "integer", "description": "معرف البضاعة بالدفتر" },
                "quantity": { "type": "integer", "description": "الكمية المشتراة" },
                "unit_price": { "type": "integer", "description": "سعر بيع القطعة بالفاتورة" }
              }
            }
          },
          "installments": {
            "type": "array",
            "description": "مصفوفة تواريخ وقيم استحقاق أقساط العميل.",
            "items": {
              "type": "object",
              "required": ["payment_date", "amount"],
              "properties": {
                "payment_date": { "type": "string", "format": "date", "description": "تاريخ القسط الشهري (قاعدة 25)" },
                "amount": { "type": "integer", "description": "مبلغ القسط المستحق" }
              }
            }
          }
        }
      },
      "ExpenseSchema": {
        "type": "object",
        "required": ["branch_id", "amount", "description"],
        "properties": {
          "id": { "type": "integer" },
          "branch_id": { "type": "integer" },
          "amount": { "type": "integer", "description": "قيمة المصروف المدفوع من الخزنة" },
          "description": { "type": "string", "description": "سبب صرف المبلغ بالتفصيل" },
          "expense_year": { "type": "integer", "example": 2026 },
          "expense_month": { "type": "integer", "example": 6 },
          "created_at": { "type": "string", "format": "date-time" }
        }
      },
      "SyncPullResponse": {
        "type": "object",
        "properties": {
          "status": { "type": "string", "example": "success" },
          "products": {
            "type": "array",
            "items": {
              "type": "object",
              "description": "بيانات البضاعة المترجمة لـ SQLite",
              "properties": {
                "id": { "type": "integer", "description": "يترجم لـ local_id" },
                "name": { "type": "string" },
                "branch_id": { "type": "integer" },
                "initial_quantity": { "type": "integer" },
                "initial_purchase_price": { "type": "integer" },
                "initial_commission_amount": { "type": "integer" },
                "initial_month": { "type": "integer" },
                "initial_year": { "type": "integer" }
              }
            }
          },
          "receipts": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "integer", "description": "يترجم لـ local_id" },
                "receipt_hash": { "type": "string" },
                "receipt_number": { "type": "integer" },
                "branch_id": { "type": "integer" },
                "salesperson_id": { "type": "integer", "nullable": true },
                "customer_name": { "type": "string" },
                "phone_number": { "type": "string", "description": "يترجم لـ customer_phone" },
                "address": { "type": "string", "description": "يترجم لـ customer_address" },
                "area": { "type": "string", "description": "يترجم لـ customer_area" },
                "total_amount": { "type": "integer" },
                "down_payment": { "type": "integer" },
                "is_cash_sale": { "type": "boolean" },
                "sale_month": { "type": "integer" },
                "sale_year": { "type": "integer" },
                "created_at": { "type": "string", "format": "date-time", "description": "يترجم لـ created_at_local" }
              }
            }
          },
          "expenses": {
            "type": "array",
            "items": { "$ref": "#/components/schemas/ExpenseSchema" }
          },
          "installments": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "integer" },
                "receipt_id": { "type": "integer" },
                "payment_month": { "type": "integer" },
                "payment_year": { "type": "integer" },
                "amount": { "type": "integer" }
              }
            }
          },
          "branches": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "integer" },
                "name": { "type": "string" }
              }
            }
          },
          "users": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "integer" },
                "name": { "type": "string" },
                "branch_id": { "type": "integer" }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 📢 7. متطلبات واجهة المستخدم ومزامنة البيانات للواجهات (React Integration)

لتفعيل الترابط السلس بين واجهة الويب والـ API:
1. **الاشتراك المنتهي (Subscription Expired):** يجب على تطبيق React التقاط رمز الخطأ `403 Forbidden` برسالة `"الاشتراك السحابي انتهى"` وتوجيه المستخدم مباشرة لصفحة تفعيل باقة الترخيص لإدخال كود الشحن الجديد.
2. **منع تعديل تواريخ الأقساط بالواجهة:** يجب على واجهة تعديل الفواتير تعطيل أي حقول تسمح بتغيير تواريخ الأقساط يدويًا، حيث يقوم السيرفر بحسابها تلقائيًا بناءً على يوم 25 في الشهور المتتالية.
3. **التصميم المتجاوب RTL:** جميع ردود فعل رسائل التأكيد والخطأ المستلمة من الـ API يجب أن تُعرض باتجاه اليمين إلى اليسار (Right-to-Left) ومتناسقة مع المصطلحات المهنية المتفق عليها في مستند التصميم.
