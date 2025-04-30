
# 🕵️ Detecting Seeding Comments on TikTok

> Đồ án môn học **IE403 - Khai thác mạng dữ liệu truyền thông**  
> Trường: UIT  
> Giảng viên: Nguyễn Văn Kiệt  
> Nhóm thực hiện: Nhóm 5

---

## 📌 Giới thiệu

Trong thời đại mạng xã hội phát triển mạnh mẽ, đặc biệt là TikTok, hành vi **seeding** (tạo bình luận giả để quảng bá, thao túng nhận thức) ngày càng phổ biến và tinh vi. Điều này ảnh hưởng đến:
- Trải nghiệm người dùng
- Độ tin cậy của các chỉ số tương tác
- Hiệu quả đánh giá các chiến dịch truyền thông

**Mục tiêu của dự án** là phát hiện các bình luận seeding dựa trên:
- Phân tích nội dung bình luận (text-based)
- Đặc trưng hành vi người dùng (behavioral features)

---

## 🎯 Mục tiêu

- Phát hiện bình luận seeding hoặc spam trên TikTok
- Hỗ trợ TikTokers, doanh nghiệp, nhà quảng cáo đánh giá chất lượng tương tác
- Xây dựng nền tảng hệ thống chống gian lận trên mạng xã hội

---

## 🛠️ Quy trình thực hiện

### 1. Thu thập dữ liệu
- **Nguồn dữ liệu:** Bình luận và người dùng từ TikTok (sử dụng API, Selenium, hoặc Apify)
- **Dữ liệu bao gồm:**
  - Video: `video_id`, `description`, `hashtags`
  - Bình luận: `comment_id`, `comment_text`, `like_count`, `timestamp`, `user_id`
  - Người dùng: `followers`, `comment_count`, `duplicate_ratio`, v.v.
- **Lưu trữ:** CSV, MongoDB hoặc PostgreSQL

### 2. Tiền xử lý dữ liệu
- **Văn bản:**
  - Xóa ký tự đặc biệt, link, emoji
  - Chuẩn hoá tiếng Việt (xóa dấu, viết thường)
  - Tách từ bằng Underthesea, Pyvi, hoặc VnCoreNLP
  - Vector hóa bằng TF-IDF, CountVectorizer hoặc embedding như FastText, PhoBERT
- **Hành vi người dùng:**
  - Tính duplicate ratio
  - Cosine similarity giữa các bình luận
  - Tần suất bình luận theo thời gian

### 3. Xây dựng mô hình
- **Mục tiêu:** Phân loại bình luận là Seeding (`1`) hoặc Không Seeding (`0`)
- **Mô hình sử dụng:**
  - Truyền thống: Random Forest, XGBoost, Logistic Regression, SVM
  - Deep Learning: LSTM, BiLSTM, PhoBERT fine-tuned
- **Input:** Văn bản và đặc trưng hành vi
- **Output:** Nhãn nhị phân

### 4. Đánh giá mô hình
- **Chia tập train/test:** 80/20
- **Nếu không có nhãn:** Gán nhãn thủ công hoặc dùng clustering (KMeans)
- **Chỉ số đánh giá:** Accuracy, Precision, Recall, F1-score, ROC-AUC
- **Trực quan hóa:** Confusion Matrix, ROC Curve, WordCloud

### 5. Triển khai ứng dụng
- **Framework:** Flask hoặc Streamlit
- **Tính năng chính:**
  - Nhập URL video TikTok
  - Dự đoán % bình luận seeding
  - Hiển thị và tải danh sách bình luận nghi vấn

---

## 🧾 Đầu ra của dự án

| Thành phần       | Mô tả |
|------------------|-------|
| Dataset          | Bình luận TikTok đã gán nhãn seeding / không seeding |
| Mô hình          | Mô hình học máy phát hiện seeding |
| Web App          | Ứng dụng kiểm tra bình luận seeding theo URL |
| Báo cáo          | Tài liệu chi tiết phương pháp và kết quả |

---

## ✅ Kết luận

Dự án mang tính ứng dụng thực tiễn cao, đặc biệt trong bối cảnh mạng xã hội ngày càng bị lạm dụng bởi các chiến dịch seeding. Hệ thống hỗ trợ các bên liên quan:
- Kiểm tra độ trung thực của tương tác
- Phát hiện hành vi gian lận
- Nâng cao độ minh bạch trên các nền tảng UGC (user-generated content)

---

## 📬 Liên hệ 

- Vũ Minh Hiếu - 22520451@gm.uit.edu.vn 
- Ngô Thị Lễ Hội - 22520491@gm.uit.edu.vn
- Nguyễn Tấn Cao Hào - 22520402@gm.uit.edu.vn
- Phạm Võ Gia Huy - 22520572@gm.uit.edu.vn