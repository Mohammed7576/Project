# Prometheus: Autonomous Genetic SQLi Evolution System

نظام متطور يعتمد على الخوارزميات الجينية والذكاء الاصطناعي لاستكشاف وتطوير ثغرات SQL Injection بشكل آلي وذكي.

## المميزات (Features)
- **Swarm Intelligence:** محاكاة ذكاء الأسراب لتوزيع مهام الاستطلاع والهجوم.
- **Deep Brain Activity:** تتبع قرارات الذكاء الاصطناعي وعمليات التعلم في الوقت الفعلي.
- **Live Swarm Radar:** رادار تفاعلي يعرض تعقيد الهجمات ومعدلات النجاح.
- **Attack Chain Builder:** واجهة بصرية لبناء سلاسل الهجمات المعقدة.
- **Sandbox Environment:** بيئة آمنة لاختبار الهجمات وتحليل الاستجابات.

## المتطلبات (Requirements)
- Node.js (v18+)
- Python (3.10+)
- SQLite3

## التنصيب (Installation)

1. قم بتحميل المستودع:
   ```bash
   git clone <your-repo-url>
   cd prometheus
   ```

2. تنصيب مكتبات Node.js:
   ```bash
   npm install
   ```

3. تنصيب مكتبات Python:
   ```bash
   pip install -r requirements.txt
   ```

4. إعداد المتغيرات البيئية:
   قم بإنشاء ملف `.env` بناءً على `.env.example` وأضف مفتاح Gemini API الخاص بك:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

## التشغيل (Usage)

لتشغيل التطبيق في وضع التطوير:
```bash
npm run dev
```

سيفتح التطبيق على الرابط: `http://localhost:3000`

## إخلاء مسؤولية (Disclaimer)
هذا المشروع للأغراض التعليمية والبحثية فقط. الاستخدام غير المصرح به لهذا النظام ضد أهداف لا تملك إذناً صريحاً بمهاجمتها هو عمل غير قانوني.

---

## License
MIT License
